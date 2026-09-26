package com.kalpa.android.screens

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.automirrored.filled.TrendingUp
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.GridView
import androidx.compose.material.icons.filled.Groups
import androidx.compose.material.icons.filled.Inventory2
import androidx.compose.material.icons.filled.LocalShipping
import androidx.compose.material.icons.filled.Store
import androidx.compose.material.icons.filled.Storefront
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.layout
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.launch

// Colors live in KalpaScreenColors.kt (same package, no import needed).
// Do not redeclare a color object in this file.

/* -------------------------------------------------------------------- */
/*  PROTOTYPE DATA (values taken from the design, not live data)        */
/* -------------------------------------------------------------------- */
private enum class Catchment(val label: String) {
    CORE("5 km Core"),
    EXTENDED("10 km Extended")
}

private enum class PillTone { GREEN, PEACH }

private data class MarketSignal(
    val title: String,
    val subtitle: String,
    val subtitleEmphasised: Boolean,
    val pillText: String,
    val pillTone: PillTone,
    val icon: ImageVector,
    val tileColor: Color,
    val iconTint: Color,
    val detail: String
)

private val marketSignals = listOf(
    MarketSignal(
        title = "Buyers nearby",
        subtitle = "3,400 kg / Day retail",
        subtitleEmphasised = false,
        pillText = "High need",
        pillTone = PillTone.GREEN,
        icon = Icons.Filled.Storefront,
        tileColor = KalpaScreenColors.OrangeBadgeBg,
        iconTint = KalpaScreenColors.Orange,
        detail = "Retail buyers around your farm ask for about 3,400 kg every day. " +
                "That is the daily demand your farm can sell into."
    ),
    MarketSignal(
        title = "Homes in reach",
        subtitle = "18,500 Homes",
        subtitleEmphasised = true,
        pillText = "15-Min",
        pillTone = PillTone.GREEN,
        icon = Icons.Filled.Groups,
        tileColor = KalpaScreenColors.PillGray,
        iconTint = KalpaScreenColors.StepUpcomingBg,
        detail = "About 18,500 homes are within a 15-minute reach of your farm. " +
                "These households are your nearest customers."
    ),
    MarketSignal(
        title = "Competitors",
        subtitle = "3 Other Farms",
        subtitleEmphasised = true,
        pillText = "Low pressure",
        pillTone = PillTone.PEACH,
        icon = Icons.Filled.Store,
        tileColor = KalpaScreenColors.PillGray,
        iconTint = KalpaScreenColors.TextPrimary,
        detail = "Only 3 other farms operate in your catchment, so you face little " +
                "pressure from competitors."
    ),
    MarketSignal(
        title = "Markets & Bazaars",
        subtitle = "6 Daily Haats",
        subtitleEmphasised = true,
        pillText = "Frequent",
        pillTone = PillTone.GREEN,
        icon = Icons.Filled.GridView,
        tileColor = KalpaScreenColors.OrangeBadgeBg,
        iconTint = KalpaScreenColors.Orange,
        detail = "6 daily haats and bazaars are close by, giving you regular places " +
                "to sell."
    ),
    MarketSignal(
        title = "Best sales seasons",
        subtitle = "+28% in Winter",
        subtitleEmphasised = true,
        pillText = "+28%",
        pillTone = PillTone.PEACH,
        icon = Icons.Filled.CalendarMonth,
        tileColor = KalpaScreenColors.OrangeSoftAlt,
        iconTint = KalpaScreenColors.OrangeDark,
        detail = "Sales run about 28% higher in winter. Plan your batches so birds are " +
                "ready for that season."
    ),
    MarketSignal(
        title = "Feed & supplies",
        subtitle = "Save ₹1.80 per kg",
        subtitleEmphasised = true,
        pillText = "Low transit",
        pillTone = PillTone.GREEN,
        icon = Icons.Filled.Inventory2,
        tileColor = KalpaScreenColors.StepDoneBg,
        iconTint = KalpaScreenColors.StepDoneIcon,
        detail = "Feed and supplies are available locally, saving about ₹1.80 per kg " +
                "compared with the Kolkata distributor."
    )
)

// Map positions are fractions (0..1) of the map area, so the layout scales
// with screen width. A real map SDK can replace CatchmentMap later.
private val siteCenter = Offset(0.476f, 0.51f)
private val buyerPoints = listOf(Offset(0.285f, 0.557f), Offset(0.766f, 0.30f))
private val otherFarmPoints = listOf(Offset(0.348f, 0.32f), Offset(0.728f, 0.51f), Offset(0.63f, 0.70f))
private val vetPoint = Offset(0.208f, 0.256f)

/* -------------------------------------------------------------------- */
/*  MAIN SCREEN                                                          */
/* -------------------------------------------------------------------- */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun YourLocalMarketScreen(
    onBackClick: () -> Unit = {},
    onContinueClick: () -> Unit = {},
    onSignalClick: (signalTitle: String) -> Unit = {},
    onFullAuditClick: () -> Unit = {}
) {
    var catchment by remember { mutableStateOf(Catchment.CORE) }
    var selectedSignal by remember { mutableStateOf<MarketSignal?>(null) }

    val blurRadius by androidx.compose.animation.core.animateDpAsState(targetValue = if (selectedSignal != null) 12.dp else 0.dp, label = "blur")
    Scaffold(
        modifier = if (blurRadius > 0.dp) Modifier.blur(blurRadius) else Modifier,
        containerColor = KalpaScreenColors.ScreenBackgroundCream,
        bottomBar = {
            Surface(color = KalpaScreenColors.ScreenBackgroundCream) {
                Box(modifier = Modifier.padding(horizontal = 20.dp, vertical = 14.dp)) {
                    Button(
                        onClick = onContinueClick,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(56.dp),
                        shape = RoundedCornerShape(30.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = KalpaScreenColors.Orange,
                            contentColor = Color.White
                        )
                    ) {
                        Text(
                            text = "See the opportunity",
                            fontSize = 17.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(Modifier.width(8.dp))
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                    }
                }
            }
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            KalpaTopBar(onBackClick = onBackClick, stepText = "Page 5 of 14")

            Column(modifier = Modifier.padding(horizontal = 20.dp)) {
                Spacer(Modifier.height(8.dp))
                Text(
                    text = "Your local area",
                    fontSize = 26.sp,
                    fontWeight = FontWeight.Bold,
                    color = KalpaScreenColors.TextPrimary
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = "What the area around your farm looks like",
                    fontSize = 14.sp,
                    color = KalpaScreenColors.TextSecondary
                )

                Spacer(Modifier.height(16.dp))

                // ---- Catchment map card --------------------------------
                Surface(
                    shape = RoundedCornerShape(20.dp),
                    color = KalpaScreenColors.CardWhite,
                    border = BorderStroke(1.dp, KalpaScreenColors.Divider),
                    shadowElevation = 2.dp,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column {
                        CatchmentSelector(
                            selected = catchment,
                            onSelect = { catchment = it }
                        )
                        CatchmentMap(catchment = catchment)
                        MapLegend()
                    }
                }

                Spacer(Modifier.height(14.dp))

                // ---- Demand / Transit ----------------------------------
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(IntrinsicSize.Min),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    MetricCard(
                        label = "DEMAND",
                        icon = Icons.AutoMirrored.Filled.TrendingUp,
                        value = "3,400 kg / Day",
                        description = "3,400 kg Daily Demand",
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxHeight()
                    )
                    MetricCard(
                        label = "TRANSIT",
                        icon = Icons.Filled.LocalShipping,
                        value = "12 Mins to Highway",
                        description = "Paved road access",
                        modifier = Modifier
                            .weight(1f)
                            .fillMaxHeight()
                    )
                }

                Spacer(Modifier.height(22.dp))

                // ---- Market signals ------------------------------------
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Market signals at a glance",
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = KalpaScreenColors.TextPrimary,
                        modifier = Modifier.weight(1f).padding(end = 8.dp),
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        text = "Tap to inspect",
                        fontSize = 13.sp,
                        color = KalpaScreenColors.TextMuted,
                        maxLines = 1,
                        softWrap = false
                    )
                }

                Spacer(Modifier.height(12.dp))

                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    marketSignals.chunked(2).forEach { rowSignals ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(IntrinsicSize.Min),
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            rowSignals.forEach { signal ->
                                SignalCard(
                                    signal = signal,
                                    onClick = {
                                        selectedSignal = signal
                                        onSignalClick(signal.title)
                                    },
                                    modifier = Modifier
                                        .weight(1f)
                                        .fillMaxHeight()
                                )
                            }
                        }
                    }
                }

                Spacer(Modifier.height(14.dp))

                VerifiedLocalProofCard(onFullAuditClick = onFullAuditClick)

                Spacer(Modifier.height(20.dp))
            }
        }
    }

    // ---- Signal detail bottom sheet -----------------------------------
    selectedSignal?.let { signal ->
        val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
        val scope = rememberCoroutineScope()
        val closeSheet: () -> Unit = {
            scope.launch { sheetState.hide() }.invokeOnCompletion {
                if (!sheetState.isVisible) selectedSignal = null
            }
        }
        ModalBottomSheet(
            onDismissRequest = { selectedSignal = null },
            sheetState = sheetState,
            containerColor = KalpaScreenColors.CardWhite,
            shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp)
        ) {
            SignalDetailSheet(signal = signal, onClose = closeSheet)
        }
    }
}



/* -------------------------------------------------------------------- */
/*  CATCHMENT SELECTOR (5 km / 10 km, real single-select state)          */
/* -------------------------------------------------------------------- */
@Composable
private fun CatchmentSelector(selected: Catchment, onSelect: (Catchment) -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(KalpaScreenColors.QuoteBg)
            .padding(horizontal = 14.dp, vertical = 10.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = "Ground Catchment",
            fontSize = 13.sp,
            fontWeight = FontWeight.SemiBold,
            color = KalpaScreenColors.TextSecondary,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier
                .weight(1f, fill = false)
                .padding(end = 8.dp)
        )
        Surface(shape = RoundedCornerShape(20.dp), color = KalpaScreenColors.CardWhite) {
            Row(modifier = Modifier.padding(3.dp)) {
                Catchment.values().forEach { option ->
                    val isSelected = option == selected
                    val bg by animateColorAsState(
                        if (isSelected) KalpaScreenColors.Orange else Color.Transparent,
                        label = "catchmentBg"
                    )
                    val fg by animateColorAsState(
                        if (isSelected) Color.White else KalpaScreenColors.TextSecondary,
                        label = "catchmentFg"
                    )
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(20.dp))
                            .background(bg)
                            .clickable { onSelect(option) }
                            .padding(horizontal = 11.dp, vertical = 7.dp)
                    ) {
                        Text(
                            text = option.label,
                            fontSize = 12.sp,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
                            color = fg,
                            maxLines = 1
                        )
                    }
                }
            }
        }
    }
}

/* -------------------------------------------------------------------- */
/*  STYLISED CATCHMENT MAP                                               */
/* -------------------------------------------------------------------- */

/** Places a child centred on a fractional point of the parent's bounds. */
private fun Modifier.anchoredAt(x: Float, y: Float): Modifier = layout { measurable, constraints ->
    val placeable = measurable.measure(constraints.copy(minWidth = 0, minHeight = 0))
    layout(constraints.maxWidth, constraints.maxHeight) {
        placeable.place(
            (constraints.maxWidth * x - placeable.width / 2f).toInt(),
            (constraints.maxHeight * y - placeable.height / 2f).toInt()
        )
    }
}

@Composable
private fun CatchmentMap(catchment: Catchment) {
    val coreFill by animateFloatAsState(
        if (catchment == Catchment.CORE) 0.12f else 0f, label = "coreFill"
    )
    val extendedFill by animateFloatAsState(
        if (catchment == Catchment.EXTENDED) 0.08f else 0f, label = "extendedFill"
    )
    val coreStroke by animateColorAsState(
        if (catchment == Catchment.CORE) KalpaScreenColors.Orange
        else KalpaScreenColors.TextMuted.copy(alpha = 0.5f),
        label = "coreStroke"
    )
    val extendedStroke by animateColorAsState(
        if (catchment == Catchment.EXTENDED) KalpaScreenColors.Orange
        else KalpaScreenColors.TextMuted.copy(alpha = 0.5f),
        label = "extendedStroke"
    )

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(270.dp)
            .background(KalpaScreenColors.MapLand)
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val w = size.width
            val h = size.height

            // Green areas
            drawCircle(KalpaScreenColors.MapGreen, w * 0.30f, Offset(w * 0.86f, h * 0.98f))
            drawCircle(
                KalpaScreenColors.MapGreen.copy(alpha = 0.6f),
                w * 0.18f,
                Offset(w * 0.02f, h * 1.0f)
            )

            // River
            val river = Path().apply {
                moveTo(0f, h * 0.10f)
                quadraticBezierTo(w * 0.5f, h * 0.16f, w, h * 0.02f)
            }
            drawPath(
                river,
                KalpaScreenColors.MapWater,
                style = Stroke(width = 9.dp.toPx(), cap = StrokeCap.Round)
            )

            // Minor road
            drawLine(
                KalpaScreenColors.StepDoneBg,
                Offset(w * 0.72f, h * 0.18f),
                Offset(w * 0.93f, h * 0.78f),
                strokeWidth = 8.dp.toPx(),
                cap = StrokeCap.Round
            )

            // Highway
            val hwStart = Offset(0f, h * 0.70f)
            val hwEnd = Offset(w, h * 0.09f)
            drawLine(KalpaScreenColors.Divider, hwStart, hwEnd, strokeWidth = 13.dp.toPx())
            drawLine(KalpaScreenColors.CardWhite, hwStart, hwEnd, strokeWidth = 9.dp.toPx())

            // Dotted path
            drawLine(
                KalpaScreenColors.TextMuted.copy(alpha = 0.6f),
                Offset(w * siteCenter.x, h * siteCenter.y),
                Offset(w * 0.60f, h * 0.92f),
                strokeWidth = 2.dp.toPx(),
                cap = StrokeCap.Round,
                pathEffect = PathEffect.dashPathEffect(floatArrayOf(3.dp.toPx(), 6.dp.toPx()))
            )

            // Catchment rings (outer = 10 km, inner = 5 km)
            val center = Offset(w * siteCenter.x, h * siteCenter.y)
            val outerRadius = minOf(w * 0.26f, h * 0.46f)
            val innerRadius = outerRadius / 2f
            val dash = PathEffect.dashPathEffect(floatArrayOf(8.dp.toPx(), 6.dp.toPx()))

            drawCircle(KalpaScreenColors.Orange.copy(alpha = extendedFill), outerRadius, center)
            drawCircle(
                extendedStroke, outerRadius, center,
                style = Stroke(width = 1.5.dp.toPx(), pathEffect = dash)
            )
            drawCircle(KalpaScreenColors.Orange.copy(alpha = coreFill), innerRadius, center)
            drawCircle(
                coreStroke, innerRadius, center,
                style = Stroke(width = 1.5.dp.toPx(), pathEffect = dash)
            )

            // Other farms
            otherFarmPoints.forEach {
                drawCircle(
                    KalpaScreenColors.StepUpcomingBg, 4.dp.toPx(),
                    Offset(w * it.x, h * it.y)
                )
            }

            // Vet & feed distributor
            drawCircle(
                KalpaScreenColors.StatusGreenText, 4.dp.toPx(),
                Offset(w * vetPoint.x, h * vetPoint.y)
            )

            // Buyers (glow + dot)
            buyerPoints.forEach {
                val p = Offset(w * it.x, h * it.y)
                drawCircle(KalpaScreenColors.Orange.copy(alpha = 0.25f), 20.dp.toPx(), p)
                drawCircle(KalpaScreenColors.Orange.copy(alpha = 0.35f), 12.dp.toPx(), p)
                drawCircle(KalpaScreenColors.OrangeDark, 4.dp.toPx(), p)
            }

            // Your site: leader line + ring + dot
            drawLine(
                KalpaScreenColors.Orange,
                Offset(center.x, h * 0.45f),
                center,
                strokeWidth = 1.5.dp.toPx()
            )
            drawCircle(KalpaScreenColors.Orange, 8.dp.toPx(), center)
            drawCircle(KalpaScreenColors.CardWhite, 3.5.dp.toPx(), center)
        }

        // Labels
        MapLabel(
            text = "Vet & Feed Distributor",
            x = 0.21f, y = 0.335f,
            background = Color.Transparent,
            contentColor = KalpaScreenColors.TextSecondary,
            bold = false
        )
        MapLabel(
            text = "GT Road Dhaba Belt",
            x = 0.29f, y = 0.645f,
            background = KalpaScreenColors.CardWhite,
            contentColor = KalpaScreenColors.TextPrimary,
            bordered = true
        )
        MapLabel(
            text = "Benachity Mandi",
            x = 0.766f, y = 0.215f,
            background = KalpaScreenColors.TextPrimary,
            contentColor = Color.White
        )
        MapLabel(
            text = "Broiler Unit B",
            x = 0.63f, y = 0.80f,
            background = KalpaScreenColors.PillGray,
            contentColor = KalpaScreenColors.TextSecondary,
            bold = false
        )
        MapLabel(
            text = "Your Site (Banskopa)",
            x = siteCenter.x, y = 0.41f,
            background = KalpaScreenColors.Orange,
            contentColor = Color.White,
            large = true
        )
    }
}

@Composable
private fun MapLabel(
    text: String,
    x: Float,
    y: Float,
    background: Color,
    contentColor: Color,
    bordered: Boolean = false,
    bold: Boolean = true,
    large: Boolean = false
) {
    Surface(
        modifier = Modifier.anchoredAt(x, y),
        shape = RoundedCornerShape(if (large) 10.dp else 8.dp),
        color = background,
        border = if (bordered) BorderStroke(1.dp, KalpaScreenColors.Divider) else null
    ) {
        Text(
            text = text,
            color = contentColor,
            fontSize = if (large) 11.sp else 10.sp,
            fontWeight = if (bold) FontWeight.Bold else FontWeight.Medium,
            maxLines = 1,
            modifier = Modifier.padding(
                horizontal = if (background == Color.Transparent) 0.dp else 8.dp,
                vertical = 3.dp
            )
        )
    }
}

@Composable
private fun MapLegend() {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 14.dp, vertical = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        LegendItem("Your Farm", KalpaScreenColors.Orange, modifier = Modifier.weight(1f))
        LegendItem("Buyers Nearby", KalpaScreenColors.Orange.copy(alpha = 0.55f), modifier = Modifier.weight(1f))
        LegendItem("3 Other Farms", KalpaScreenColors.StepUpcomingBg, modifier = Modifier.weight(1f))
    }
}

@Composable
private fun LegendItem(label: String, dotColor: Color, modifier: Modifier = Modifier) {
    Row(verticalAlignment = Alignment.CenterVertically, modifier = modifier.padding(end = 4.dp)) {
        Box(
            modifier = Modifier
                .size(9.dp)
                .clip(CircleShape)
                .background(dotColor)
        )
        Spacer(Modifier.width(6.dp))
        Text(
            text = label,
            fontSize = 12.sp,
            color = KalpaScreenColors.TextSecondary,
            modifier = Modifier.weight(1f),
            maxLines = 1
        )
    }
}

/* -------------------------------------------------------------------- */
/*  METRIC CARD (Demand / Transit)                                       */
/* -------------------------------------------------------------------- */
@Composable
private fun MetricCard(
    label: String,
    icon: ImageVector,
    value: String,
    description: String,
    modifier: Modifier = Modifier
) {
    Surface(
        shape = RoundedCornerShape(14.dp),
        color = KalpaScreenColors.CardWhite,
        border = BorderStroke(1.dp, KalpaScreenColors.Divider),
        shadowElevation = 1.dp,
        modifier = modifier
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = label,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold,
                    letterSpacing = 0.6.sp,
                    color = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.weight(1f).padding(end = 4.dp)
                )
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.size(20.dp)
                )
            }
            Spacer(Modifier.height(8.dp))
            Text(
                text = value,
                fontSize = 19.sp,
                lineHeight = 25.sp,
                fontWeight = FontWeight.Bold,
                color = KalpaScreenColors.TextPrimary
            )
            Spacer(Modifier.height(4.dp))
            Text(
                text = description,
                fontSize = 13.sp,
                color = KalpaScreenColors.TextSecondary
            )
        }
    }
}

/* -------------------------------------------------------------------- */
/*  SIGNAL CARD + STATUS PILL                                            */
/* -------------------------------------------------------------------- */
@Composable
private fun SignalCard(
    signal: MarketSignal,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        shape = RoundedCornerShape(14.dp),
        color = KalpaScreenColors.CardWhite,
        border = BorderStroke(1.dp, KalpaScreenColors.Divider),
        shadowElevation = 1.dp,
        modifier = modifier
    ) {
        Column(
            modifier = Modifier
                .clickable(onClick = onClick)
                .padding(14.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                SignalIconTile(signal)
                Spacer(Modifier.width(8.dp))
                StatusPill(text = signal.pillText, tone = signal.pillTone, modifier = Modifier.weight(1f, fill = false))
            }
            Spacer(Modifier.height(12.dp))
            Text(
                text = signal.title,
                fontSize = 17.sp,
                fontWeight = FontWeight.SemiBold,
                color = KalpaScreenColors.TextPrimary
            )
            Spacer(Modifier.height(2.dp))
            Text(
                text = signal.subtitle,
                fontSize = 12.sp,
                fontWeight = if (signal.subtitleEmphasised) FontWeight.SemiBold else FontWeight.Normal,
                color = if (signal.subtitleEmphasised) KalpaScreenColors.OrangeDark
                else KalpaScreenColors.TextSecondary
            )
        }
    }
}

@Composable
private fun SignalIconTile(signal: MarketSignal) {
    Box(
        modifier = Modifier
            .size(40.dp)
            .clip(RoundedCornerShape(10.dp))
            .background(signal.tileColor),
        contentAlignment = Alignment.Center
    ) {
        Icon(
            imageVector = signal.icon,
            contentDescription = null,
            tint = signal.iconTint,
            modifier = Modifier.size(22.dp)
        )
    }
}

@Composable
private fun StatusPill(text: String, tone: PillTone, modifier: Modifier = Modifier) {
    val bg = if (tone == PillTone.GREEN) KalpaScreenColors.StatusGreenBg
    else KalpaScreenColors.OrangeBadgeBg
    val fg = if (tone == PillTone.GREEN) KalpaScreenColors.StatusGreenText
    else KalpaScreenColors.OrangeDark
    Surface(shape = RoundedCornerShape(20.dp), color = bg, modifier = modifier) {
        Text(
            text = text,
            fontSize = 11.sp,
            fontWeight = FontWeight.Medium,
            color = fg,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
        )
    }
}

/* -------------------------------------------------------------------- */
/*  VERIFIED LOCAL PROOF                                                 */
/* -------------------------------------------------------------------- */
@Composable
private fun VerifiedLocalProofCard(onFullAuditClick: () -> Unit) {
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = KalpaScreenColors.CardWhite,
        border = BorderStroke(1.dp, KalpaScreenColors.Divider),
        shadowElevation = 1.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(36.dp)
                        .clip(CircleShape)
                        .background(KalpaScreenColors.IconCircleBg),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Outlined.CheckCircle,
                        contentDescription = null,
                        tint = KalpaScreenColors.Orange,
                        modifier = Modifier.size(20.dp)
                    )
                }
                Spacer(Modifier.width(10.dp))
                Text(
                    text = "VERIFIED LOCAL PROOF",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.SemiBold,
                    letterSpacing = 0.4.sp,
                    color = KalpaScreenColors.OrangeDark,
                    modifier = Modifier.weight(1f)
                )
                Row(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .clickable(onClick = onFullAuditClick)
                        .padding(4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Full audit",
                        fontSize = 13.sp,
                        color = KalpaScreenColors.TextSecondary
                    )
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.KeyboardArrowRight,
                        contentDescription = null,
                        tint = KalpaScreenColors.TextSecondary,
                        modifier = Modifier.size(18.dp)
                    )
                }
            }

            Spacer(Modifier.height(12.dp))
            Text(
                text = "Chick hatcheries and feed stores are located in Andal. " +
                        "If you run short, new stock reaches your farm in under 2 hours.",
                fontSize = 14.sp,
                lineHeight = 20.sp,
                color = KalpaScreenColors.TextPrimary
            )

            Spacer(Modifier.height(12.dp))
            Surface(
                shape = RoundedCornerShape(10.dp),
                color = KalpaScreenColors.FieldGray,
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .height(IntrinsicSize.Min)
                        .padding(12.dp)
                ) {
                    ProofColumn(
                        label = "Local Sourcing",
                        value = "Save ₹1.80 per kg",
                        valueColor = KalpaScreenColors.OrangeDark,
                        footnote = "Andal Depot",
                        footnoteColor = KalpaScreenColors.StatusGreenText,
                        modifier = Modifier.weight(1f)
                    )
                    Box(
                        modifier = Modifier
                            .padding(horizontal = 10.dp)
                            .width(1.dp)
                            .fillMaxHeight()
                            .background(KalpaScreenColors.Divider)
                    )
                    ProofColumn(
                        label = "Kolkata Distributor",
                        value = "+₹1.80 Transit",
                        valueColor = KalpaScreenColors.TextPrimary,
                        footnote = "6+ hrs delay",
                        footnoteColor = KalpaScreenColors.DelayRed,
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }
    }
}

@Composable
private fun ProofColumn(
    label: String,
    value: String,
    valueColor: Color,
    footnote: String,
    footnoteColor: Color,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier) {
        Text(text = label, fontSize = 12.sp, color = KalpaScreenColors.TextSecondary)
        Spacer(Modifier.height(2.dp))
        Text(
            text = value,
            fontSize = 16.sp,
            fontWeight = FontWeight.Bold,
            color = valueColor
        )
        Spacer(Modifier.height(2.dp))
        Text(text = footnote, fontSize = 12.sp, color = footnoteColor)
    }
}

/* -------------------------------------------------------------------- */
/*  SIGNAL DETAIL BOTTOM-SHEET CONTENT                                   */
/* -------------------------------------------------------------------- */
@Composable
private fun SignalDetailSheet(signal: MarketSignal, onClose: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .navigationBarsPadding()
            .padding(horizontal = 20.dp)
            .padding(bottom = 20.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            SignalIconTile(signal)
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = signal.title,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                    color = KalpaScreenColors.TextPrimary
                )
                Text(
                    text = signal.subtitle,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = KalpaScreenColors.OrangeDark
                )
            }
            StatusPill(text = signal.pillText, tone = signal.pillTone)
        }
        Spacer(Modifier.height(16.dp))
        Text(
            text = signal.detail,
            fontSize = 14.sp,
            lineHeight = 21.sp,
            color = KalpaScreenColors.TextPrimary
        )
        Spacer(Modifier.height(20.dp))
        Button(
            onClick = onClose,
            modifier = Modifier
                .fillMaxWidth()
                .height(50.dp),
            shape = RoundedCornerShape(30.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = KalpaScreenColors.Orange,
                contentColor = Color.White
            )
        ) {
            Text("Got it", fontSize = 16.sp, fontWeight = FontWeight.Bold)
        }
    }
}

@Preview(showBackground = true, heightDp = 1100)
@Composable
private fun YourLocalMarketScreenPreview() {
    YourLocalMarketScreen()
}