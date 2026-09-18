package com.kalpa.android.screens
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowForward
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Storefront
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.Edit
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.outlined.Sell
import androidx.compose.material.icons.outlined.Work
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// ---------- Palette (kept consistent with the landing page) ----------
private val BackgroundCream = Color(0xFFF8F4EC)
private val TopBarBeige = Color(0xFFEFE8DA)
private val OrangePrimary = Color(0xFFDB8B1F)
private val OrangeText = Color(0xFFC77E1B)
private val TextBlack = Color(0xFF1C1B19)
private val TextGraySubtle = Color(0xFF9C9385)
private val AvatarBrown = Color(0xFF5B3E22)
private val BorderGray = Color(0xFFE6E0D4)
private val CardIconBgOrange = Color(0xFFF6E9D2)
private val CardIconBgGray = Color(0xFFEFEBE2)
private val RingOuter = Color(0xFFF1DDB0)
private val RingInner = Color(0xFFF6EBD3)

@Composable
fun BusinessIntakeScreen() {
    Surface(modifier = Modifier.fillMaxSize(), color = BackgroundCream) {
        Column(modifier = Modifier.fillMaxSize()) {
            IntakeTopBar()
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp)
            ) {
                Spacer(modifier = Modifier.height(20.dp))
                Text(
                    text = "Tell KALPA about your business",
                    color = TextBlack,
                    fontSize = 22.sp,
                    fontWeight = FontWeight.ExtraBold,
                    lineHeight = 28.sp
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Speak abour or type your idea below.",
                    color = TextGraySubtle,
                    fontSize = 14.sp
                )
                Spacer(modifier = Modifier.height(28.dp))
                MicSection()
                Spacer(modifier = Modifier.height(28.dp))
                Text(
                    text = "OR TYPE YOUR BUSINESS IDEA",
                    color = TextGraySubtle,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold,
                    letterSpacing = 0.8.sp
                )
                Spacer(modifier = Modifier.height(10.dp))
                BusinessIdeaInput()
                Spacer(modifier = Modifier.height(24.dp))
                WhatIUnderstoodSection()
                Spacer(modifier = Modifier.height(24.dp))
                LooksRightButton()
                Spacer(modifier = Modifier.height(10.dp))
                Text(
                    text = "I'll ask for anything important that's missing.",
                    color = TextGraySubtle,
                    fontSize = 12.sp,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(20.dp))
            }
        }
    }
}

@Composable
private fun IntakeTopBar() {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(TopBarBeige)
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                imageVector = Icons.Default.ArrowBack,
                contentDescription = "Back",
                tint = TextBlack,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(14.dp))
            Surface(
                shape = RoundedCornerShape(50),
                color = Color.White,
                border = androidx.compose.foundation.BorderStroke(1.dp, BorderGray)
            ) {
                Text(
                    text = "STEP 1 OF 5",
                    color = TextBlack,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.SemiBold,
                    letterSpacing = 0.5.sp,
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
                )
            }
        }

        Row(verticalAlignment = Alignment.CenterVertically) {
            Surface(
                shape = RoundedCornerShape(50),
                color = Color.White,
                border = androidx.compose.foundation.BorderStroke(1.dp, BorderGray),
                modifier = Modifier.height(34.dp)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.Language,
                        contentDescription = "Language",
                        tint = TextBlack,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(text = "English", color = TextBlack, fontSize = 13.sp)
                    Spacer(modifier = Modifier.width(2.dp))
                    Icon(
                        imageVector = Icons.Default.KeyboardArrowDown,
                        contentDescription = null,
                        tint = TextBlack,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }
            Spacer(modifier = Modifier.width(10.dp))
            Box(
                modifier = Modifier
                    .size(34.dp)
                    .clip(CircleShape)
                    .background(AvatarBrown),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Person,
                    contentDescription = "Profile",
                    tint = Color.White,
                    modifier = Modifier.size(18.dp)
                )
            }
        }
    }
}

@Composable
private fun MicSection() {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.fillMaxWidth()
    ) {
        // Clean concentric rings replace the blurred halo from the original screenshot.
        Box(contentAlignment = Alignment.Center) {
            Box(
                modifier = Modifier
                    .size(120.dp)
                    .clip(CircleShape)
                    .background(RingOuter)
            )
            Box(
                modifier = Modifier
                    .size(92.dp)
                    .clip(CircleShape)
                    .background(RingInner)
            )
            Box(
                modifier = Modifier
                    .size(68.dp)
                    .clip(CircleShape)
                    .background(OrangePrimary)
                    .border(width = 3.dp, color = Color.White, shape = CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Mic,
                    contentDescription = "Speak",
                    tint = Color.White,
                    modifier = Modifier.size(28.dp)
                )
            }
        }
        Spacer(modifier = Modifier.height(14.dp))
        Text(
            text = "Tap & speak in any language",
            color = TextBlack,
            fontSize = 14.sp,
            fontWeight = FontWeight.SemiBold,
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(6.dp))
        Text(
            text = "\"I want to open a small poultry business in my village…\"",
            color = TextGraySubtle,
            fontSize = 12.sp,
            fontStyle = FontStyle.Italic,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(horizontal = 12.dp)
        )
    }
}

@Composable
private fun BusinessIdeaInput() {
    var text by remember { mutableStateOf("") }
    OutlinedTextField(
        value = text,
        onValueChange = { text = it },
        placeholder = { Text(text = "Tell us about your business...", color = TextGraySubtle, fontSize = 14.sp) },
        trailingIcon = {
            Icon(
                imageVector = Icons.Default.Mic,
                contentDescription = "Voice input",
                tint = TextGraySubtle,
                modifier = Modifier.size(20.dp)
            )
        },
        shape = RoundedCornerShape(16.dp),
        colors = OutlinedTextFieldDefaults.colors(
            focusedContainerColor = Color.White,
            unfocusedContainerColor = Color.White,
            focusedBorderColor = OrangePrimary,
            unfocusedBorderColor = BorderGray
        ),
        keyboardOptions = KeyboardOptions.Default,
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp)
    )
}

@Composable
private fun WhatIUnderstoodSection() {
    Column {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(6.dp)
                    .clip(CircleShape)
                    .background(TextBlack)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = "WHAT I UNDERSTOOD",
                color = TextBlack,
                fontSize = 12.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = 0.8.sp
            )
        }
        Spacer(modifier = Modifier.height(12.dp))

        Surface(
            shape = RoundedCornerShape(18.dp),
            color = Color.White,
            border = androidx.compose.foundation.BorderStroke(1.dp, BorderGray),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column {
                UnderstoodRow("BUSINESS", "Poultry farming", Icons.Default.Storefront, CardIconBgOrange, provided = true, isRupee = false)
                RowDivider()
                UnderstoodRow("LOCATION", "Not provided yet", Icons.Outlined.LocationOn, CardIconBgGray, provided = false, isRupee = false)
                RowDivider()
                UnderstoodRow("CAPITAL", "₹2,00,000", null, CardIconBgOrange, provided = true, isRupee = true)
                RowDivider()
                UnderstoodRow("BUSINESS TYPE", "New business", Icons.Outlined.Sell, CardIconBgOrange, provided = true, isRupee = false)
                RowDivider()
                UnderstoodRow("EXPERIENCE", "Not provided yet", Icons.Outlined.Work, CardIconBgGray, provided = false, isRupee = false)
            }
        }
    }
}

@Composable
private fun RowDivider() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(1.dp)
            .background(BorderGray)
    )
}

@Composable
private fun UnderstoodRow(
    label: String,
    value: String,
    icon: ImageVector?,
    iconBg: Color,
    provided: Boolean,
    isRupee: Boolean
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(36.dp)
                .clip(RoundedCornerShape(10.dp))
                .background(iconBg),
            contentAlignment = Alignment.Center
        ) {
            if (isRupee) {
                Text(text = "₹", color = OrangeText, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            } else if (icon != null) {
                Icon(
                    imageVector = icon,
                    contentDescription = label,
                    tint = if (provided) OrangeText else TextGraySubtle,
                    modifier = Modifier.size(18.dp)
                )
            }
        }
        Spacer(modifier = Modifier.width(12.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = label,
                color = TextGraySubtle,
                fontSize = 11.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = 0.4.sp
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = value,
                color = if (provided) TextBlack else TextGraySubtle,
                fontSize = 14.sp,
                fontWeight = if (provided) FontWeight.SemiBold else FontWeight.Normal,
                fontStyle = if (provided) FontStyle.Normal else FontStyle.Italic
            )
        }
        Icon(
            imageVector = if (provided) Icons.Outlined.Edit else Icons.Outlined.Add,
            contentDescription = if (provided) "Edit" else "Add",
            tint = if (provided) TextGraySubtle else OrangeText,
            modifier = Modifier.size(18.dp)
        )
    }
}

@Composable
private fun LooksRightButton() {
    Button(
        onClick = { /* TODO: navigate to step 2 */ },
        modifier = Modifier
            .fillMaxWidth()
            .height(56.dp),
        shape = RoundedCornerShape(16.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = OrangePrimary,
            contentColor = Color.White
        )
    ) {
        Text(text = "Looks right", fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
        Spacer(modifier = Modifier.width(8.dp))
        Icon(
            imageVector = Icons.Default.ArrowForward,
            contentDescription = null,
            modifier = Modifier.size(18.dp)
        )
    }
}

@Preview(showBackground = true, widthDp = 360, heightDp = 800)
@Composable
fun BusinessIntakeScreenPreview() {
    MaterialTheme {
        BusinessIntakeScreen()
    }
}
