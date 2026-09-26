package com.kalpa.android.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * A globally unified TopBar for KALPA screens.
 * Features a left-aligned back button and a center-aligned "Page X of Y" step badge.
 * Does NOT contain large screen titles (those remain in the screen content).
 */
@Composable
fun KalpaTopBar(
    onBackClick: () -> Unit,
    stepText: String? = null,
    trailingContent: @Composable (() -> Unit)? = null
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Back Button
        IconButton(
            onClick = onBackClick,
            modifier = Modifier
                .size(40.dp)
                .background(KalpaScreenColors.PillGray, CircleShape)
        ) {
            Icon(
                imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                contentDescription = "Back",
                tint = KalpaScreenColors.TextPrimary
            )
        }
        
        Spacer(Modifier.weight(1f))

        // Center Step Badge
        if (stepText != null) {
            Surface(
                shape = RoundedCornerShape(20.dp),
                color = KalpaScreenColors.OrangeBadgeBg
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
                ) {
                    Box(modifier = Modifier.size(6.dp).background(KalpaScreenColors.OrangeDark, CircleShape))
                    Spacer(Modifier.width(6.dp))
                    Text(
                        text = stepText.uppercase(),
                        color = KalpaScreenColors.OrangeDark,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                }
            }
        }
        
        Spacer(Modifier.weight(1f))
        
        // Trailing Content or balance spacer
        if (trailingContent != null) {
            trailingContent()
        } else {
            // Empty box to balance the center alignment
            Spacer(Modifier.size(40.dp))
        }
    }
}
