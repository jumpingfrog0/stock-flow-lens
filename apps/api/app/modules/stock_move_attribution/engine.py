from statistics import mean

from app.modules.stock_move_attribution.evidence import (
    IndexSnapshot,
    StockAttributionContext,
)
from app.modules.stock_move_attribution.schemas import (
    AnnouncementItem,
    CounterfactualCheck,
    DriverEvidence,
    IndustryContext,
    MarketBenchmark,
    MarketBreadth,
    MarketContext,
    StockMoveAttributionResponse,
    StockMoveSnapshot,
    StyleContext,
)


METHODOLOGY_VERSION = "1.0.0"


GROWTH_INDUSTRY_KEYWORDS = (
    "半导体",
    "电子",
    "软件",
    "计算机",
    "通信",
    "光学",
    "自动化",
    "机器人",
)
DEFENSIVE_VALUE_INDUSTRY_KEYWORDS = (
    "养殖",
    "农林",
    "食品",
    "饮料",
    "银行",
    "保险",
    "证券",
    "煤炭",
    "医药",
    "零售",
    "交通运输",
    "公用事业",
)


class StockMoveAttributionEngine:
    """Deterministic and side-effect-free stock move attribution rules."""

    def analyze(self, context: StockAttributionContext) -> StockMoveAttributionResponse:
        stock = context.stock
        index_map = {item.key: item for item in context.indexes}
        benchmark = _select_benchmark(stock.code, index_map)
        market_relative = (
            stock.change_pct - benchmark.change_pct if benchmark is not None else None
        )
        industry_relative = (
            stock.change_pct - context.industry.change_pct
            if context.industry is not None and context.industry.change_pct is not None
            else None
        )
        style_bucket = _classify_style(stock.industry)
        style = _build_style_context(context.indexes)
        market = _build_market_context(context, benchmark)
        industry = _build_industry_context(context)
        announcements = [
            AnnouncementItem(
                title=item.title,
                noticeDate=item.notice_date,
                artCode=item.art_code,
                sameDay=item.notice_date == stock.trade_date,
            )
            for item in context.announcements[:5]
        ]
        drivers = _score_drivers(
            context=context,
            style=style,
            style_bucket=style_bucket,
            industry_relative=industry_relative,
            announcements=announcements,
        )
        primary_driver, confidence = _select_primary_driver(
            stock.change_pct,
            drivers,
            context,
        )
        counterfactuals = _build_counterfactuals(
            context=context,
            style=style,
            style_bucket=style_bucket,
            announcements=announcements,
        )
        return StockMoveAttributionResponse(
            methodologyVersion=METHODOLOGY_VERSION,
            source=context.source,
            asOf=stock.trade_date,
            primaryDriver=primary_driver,
            confidence=confidence,
            summary=_summary_for(primary_driver),
            stock=StockMoveSnapshot(
                code=stock.code,
                name=stock.name,
                tradeDate=stock.trade_date,
                industry=stock.industry,
                styleBucket=style_bucket,
                closePrice=stock.close_price,
                changePct=stock.change_pct,
                openPrice=stock.open_price,
                highPrice=stock.high_price,
                lowPrice=stock.low_price,
                previousClose=stock.previous_close,
                amount=stock.amount,
                turnoverRate=stock.turnover_rate,
                volumeRatio=stock.volume_ratio,
                mainNetInflow=stock.main_net_inflow,
                marketRelativePct=market_relative,
                industryRelativePct=industry_relative,
            ),
            market=market,
            style=style,
            industry=industry,
            announcements=announcements,
            drivers=drivers,
            counterfactuals=counterfactuals,
            warnings=context.warnings
            + ["归因基于可观测行情和规则评分，不代表已知每笔交易的真实动机"],
        )


def _select_benchmark(
    code: str, indexes: dict[str, IndexSnapshot]
) -> IndexSnapshot | None:
    if code.startswith("688"):
        preferred = "star50"
    elif code.startswith(("300", "301")):
        preferred = "chinext"
    elif code.startswith(("600", "601", "603", "605")):
        preferred = "shanghai"
    else:
        preferred = "shenzhen"
    return indexes.get(preferred) or indexes.get("csi300") or next(iter(indexes.values()), None)


def _build_market_context(
    context: StockAttributionContext, benchmark: IndexSnapshot | None
) -> MarketContext:
    if benchmark is None:
        benchmark_key = "unknown"
        benchmark_name = "暂无基准"
        benchmark_change = 0.0
    else:
        benchmark_key = benchmark.key
        benchmark_name = benchmark.name
        benchmark_change = benchmark.change_pct
    breadth = None
    if context.breadth is not None and context.breadth.total:
        breadth = MarketBreadth(
            total=context.breadth.total,
            advancing=context.breadth.advancing,
            declining=context.breadth.declining,
            flat=context.breadth.flat,
            advancingRatio=context.breadth.advancing / context.breadth.total,
        )
    return MarketContext(
        benchmarkKey=benchmark_key,
        benchmarkName=benchmark_name,
        benchmarkChangePct=benchmark_change,
        benchmarks=[
            MarketBenchmark(
                key=item.key,
                name=item.name,
                group=item.group,
                changePct=item.change_pct,
            )
            for item in context.indexes
        ],
        breadth=breadth,
    )


def _build_style_context(indexes: list[IndexSnapshot]) -> StyleContext:
    growth_values = [item.change_pct for item in indexes if item.group == "growth"]
    value_values = [item.change_pct for item in indexes if item.group == "value"]
    growth = mean(growth_values) if growth_values else None
    value = mean(value_values) if value_values else None
    spread = value - growth if value is not None and growth is not None else None
    if growth is not None and spread is not None and growth < 0 and spread >= 1.5:
        rotation = "high_to_low"
        note = "成长代理指数走弱且价值代理显著占优，市场存在高低切换特征"
    elif growth is not None and spread is not None and growth > 0 and spread <= -1.5:
        rotation = "low_to_high"
        note = "成长代理指数显著占优，市场风险偏好向高弹性方向切换"
    else:
        rotation = "balanced"
        note = "成长与价值代理的差异尚不足以确认明确风格切换"
    return StyleContext(
        rotation=rotation,
        growthProxyChangePct=growth,
        valueProxyChangePct=value,
        valueMinusGrowthPct=spread,
        note=note,
    )


def _build_industry_context(context: StockAttributionContext) -> IndustryContext | None:
    item = context.industry
    if item is None:
        return None
    advancing_ratio = item.advancing / item.peer_count if item.peer_count else None
    return IndustryContext(
        code=item.code,
        name=item.name,
        changePct=item.change_pct,
        mainNetInflow=item.main_net_inflow,
        peerCount=item.peer_count,
        advancing=item.advancing,
        declining=item.declining,
        flat=item.flat,
        advancingRatio=advancing_ratio,
        medianChangePct=item.median_change_pct,
    )


def _score_drivers(
    context: StockAttributionContext,
    style: StyleContext,
    style_bucket: str,
    industry_relative: float | None,
    announcements: list[AnnouncementItem],
) -> list[DriverEvidence]:
    stock = context.stock
    move_positive = stock.change_pct > 0
    industry = context.industry
    rotation_relevant = _rotation_relevant(
        style.rotation,
        style_bucket,
        move_positive,
    )

    rotation_score = 0
    rotation_evidence: list[str] = []
    rotation_limitations: list[str] = []
    if rotation_relevant:
        rotation_score += 55
        rotation_evidence.append(style.note)
    else:
        rotation_limitations.append("当前风格切换方向与股票行业风格标签未形成直接对应")
    if style.valueMinusGrowthPct is not None and abs(style.valueMinusGrowthPct) >= 2.5:
        rotation_score += 15
        rotation_evidence.append(
            f"价值与成长代理涨跌差达到 {style.valueMinusGrowthPct:.2f} 个百分点"
        )
    if industry is not None and _same_direction(industry.change_pct, stock.change_pct):
        rotation_score += 15
        rotation_evidence.append("所属行业与个股同向，轮动资金存在行业落点")
    if context.breadth is not None and context.breadth.total:
        support_ratio = (
            context.breadth.advancing / context.breadth.total
            if move_positive
            else context.breadth.declining / context.breadth.total
        )
        if support_ratio >= 0.55:
            rotation_score += 15
            rotation_evidence.append(f"全市场同方向股票占比为 {support_ratio:.1%}")
    else:
        rotation_limitations.append("缺少全市场涨跌家数")

    industry_score = 0
    industry_evidence: list[str] = []
    industry_limitations: list[str] = []
    if industry is None:
        industry_limitations.append("未匹配到行业板块")
    else:
        if _same_direction(industry.change_pct, stock.change_pct):
            industry_score += 35
            industry_evidence.append(
                f"{industry.name}板块涨跌幅与个股同向"
            )
        peer_support = _peer_support_ratio(industry, move_positive)
        if peer_support is not None and peer_support >= 0.6:
            industry_score += 25
            industry_evidence.append(f"同行同方向比例为 {peer_support:.1%}")
        if _same_direction(industry.main_net_inflow, stock.change_pct):
            industry_score += 20
            industry_evidence.append("行业主力资金方向与个股涨跌一致")
        if industry_relative is not None and abs(industry_relative) <= 1.5:
            industry_score += 20
            industry_evidence.append("个股相对行业涨跌偏差较小，行业可解释度较高")

    stock_score = 0
    stock_evidence: list[str] = []
    stock_limitations: list[str] = []
    if industry_relative is not None and abs(industry_relative) >= 1.5:
        stock_score += 35
        stock_evidence.append(
            f"个股相对行业异常收益为 {industry_relative:.2f} 个百分点"
        )
    elif industry_relative is None:
        stock_limitations.append("缺少行业基准，个股异常收益无法完整计算")
    if _same_direction(stock.main_net_inflow, stock.change_pct):
        stock_score += 20
        stock_evidence.append("个股主力资金方向与股价涨跌一致")
    else:
        stock_limitations.append("当日资金流未形成同向确认或尚未更新")
    if stock.volume_ratio is not None and stock.volume_ratio >= 1.2:
        stock_score += 15
        stock_evidence.append(f"量比为 {stock.volume_ratio:.2f}，成交活跃度提升")
    if stock.turnover_rate is not None and stock.turnover_rate >= 2:
        stock_score += 10
        stock_evidence.append(f"换手率为 {stock.turnover_rate:.2f}%")
    same_day = [item for item in announcements if item.sameDay]
    if same_day:
        stock_score += 30
        stock_evidence.append(f"当日存在 {len(same_day)} 条公司公告，需进一步判断公告方向")
    elif announcements:
        stock_limitations.append("当日未发现新增公司公告，旧公告不能直接充当点火因素")
    else:
        stock_limitations.append("公告数据不可用或近期无公告")

    return sorted(
        [
            DriverEvidence(
                code="market_rotation",
                label="市场风格切换",
                score=min(rotation_score, 100),
                evidence=rotation_evidence,
                limitations=rotation_limitations,
            ),
            DriverEvidence(
                code="industry_move",
                label="行业板块共振",
                score=min(industry_score, 100),
                evidence=industry_evidence,
                limitations=industry_limitations,
            ),
            DriverEvidence(
                code="stock_specific",
                label="个股独立驱动",
                score=min(stock_score, 100),
                evidence=stock_evidence,
                limitations=stock_limitations,
            ),
        ],
        key=lambda item: item.score,
        reverse=True,
    )


def _select_primary_driver(
    change_pct: float,
    drivers: list[DriverEvidence],
    context: StockAttributionContext,
) -> tuple[str, str]:
    if abs(change_pct) < 0.3 or not drivers or drivers[0].score < 40:
        return "insufficient", "low"
    top = drivers[0]
    second = drivers[1]
    if top.score - second.score <= 10:
        primary = "mixed"
    else:
        primary = top.code
    completeness = sum(
        (
            bool(context.indexes),
            context.breadth is not None,
            context.industry is not None,
            bool(context.announcements),
            context.stock.main_net_inflow is not None,
        )
    )
    if top.score >= 75 and top.score - second.score >= 15 and completeness >= 4:
        confidence = "high"
    elif top.score >= 50 and completeness >= 3:
        confidence = "medium"
    else:
        confidence = "low"
    return primary, confidence


def _build_counterfactuals(
    context: StockAttributionContext,
    style: StyleContext,
    style_bucket: str,
    announcements: list[AnnouncementItem],
) -> list[CounterfactualCheck]:
    move_positive = context.stock.change_pct > 0
    if context.industry is None:
        peer_result = "unknown"
        peer_conclusion = "缺少同行数据，无法判断是否为个股独立行情"
    else:
        ratio = _peer_support_ratio(context.industry, move_positive)
        if ratio is not None and ratio >= 0.6:
            peer_result = "supports"
            peer_conclusion = f"{ratio:.1%} 的同行同方向，削弱纯个股消息解释"
        elif ratio is not None and ratio <= 0.4:
            peer_result = "weakens"
            peer_conclusion = f"仅 {ratio:.1%} 的同行同方向，增强个股独立因素解释"
        else:
            peer_result = "unknown"
            peer_conclusion = "同行分化，行业共振证据不足"

    if _rotation_relevant(style.rotation, style_bucket, move_positive):
        style_result = "supports"
        style_conclusion = "市场风格切换与股票涨跌方向及行业风格一致"
    elif style.rotation == "balanced":
        style_result = "unknown"
        style_conclusion = "未检测到明确风格切换"
    else:
        style_result = "weakens"
        style_conclusion = "市场风格切换方向与股票行业风格不一致"

    if any(item.sameDay for item in announcements):
        announcement_result = "supports"
        announcement_conclusion = "存在当日公司公告，需继续阅读公告判断个股催化"
    elif announcements:
        announcement_result = "weakens"
        announcement_conclusion = "当日无新增公司公告，不应把旧公告当作直接催化"
    else:
        announcement_result = "unknown"
        announcement_conclusion = "公告数据不足"

    return [
        CounterfactualCheck(
            code="peers_move_together",
            result=peer_result,
            conclusion=peer_conclusion,
        ),
        CounterfactualCheck(
            code="style_rotation",
            result=style_result,
            conclusion=style_conclusion,
        ),
        CounterfactualCheck(
            code="same_day_announcement",
            result=announcement_result,
            conclusion=announcement_conclusion,
        ),
    ]


def _classify_style(industry: str | None) -> str:
    if not industry:
        return "unclassified"
    if any(keyword in industry for keyword in GROWTH_INDUSTRY_KEYWORDS):
        return "growth"
    if any(keyword in industry for keyword in DEFENSIVE_VALUE_INDUSTRY_KEYWORDS):
        return "defensive_value"
    return "unclassified"


def _rotation_relevant(
    rotation: str,
    style_bucket: str,
    move_positive: bool,
) -> bool:
    if rotation == "high_to_low":
        return (style_bucket == "defensive_value" and move_positive) or (
            style_bucket == "growth" and not move_positive
        )
    if rotation == "low_to_high":
        return (style_bucket == "growth" and move_positive) or (
            style_bucket == "defensive_value" and not move_positive
        )
    return False


def _same_direction(value: float | None, stock_change: float) -> bool:
    if value is None or value == 0 or stock_change == 0:
        return False
    return (value > 0) == (stock_change > 0)


def _peer_support_ratio(industry, move_positive: bool) -> float | None:
    if not industry.peer_count:
        return None
    supporting = industry.advancing if move_positive else industry.declining
    return supporting / industry.peer_count


def _summary_for(primary_driver: str) -> str:
    return {
        "market_rotation": "市场风格切换是一级驱动，行业共振与个股交易结构是放大因素。",
        "industry_move": "行业板块共振是一级驱动，需结合个股相对行业强度判断独立催化。",
        "stock_specific": "个股独立因素是一级驱动，应优先核查当日公告、新闻和异常资金。",
        "mixed": "市场、行业与个股证据接近，当前更适合判断为混合驱动。",
        "insufficient": "现有可观测证据不足以给出可靠的一级驱动。",
    }[primary_driver]
