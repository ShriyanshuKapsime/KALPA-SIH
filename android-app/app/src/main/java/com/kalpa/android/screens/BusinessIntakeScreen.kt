package com.kalpa.android.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import android.Manifest
import android.content.pm.PackageManager
import android.widget.Toast
import androidx.core.content.ContextCompat
import androidx.compose.ui.platform.LocalContext
import com.kalpa.android.utils.AudioRecorderHelper
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.ArrowUpward
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// Colors now live in KalpaScreenColors.kt (same package, no import needed).
// Do not redeclare a color object in this file — see that file's header comment.

private val availableLanguages = listOf("English", "हिन्दी", "தமிழ்", "తెలుగు", "मराठी")

/* -------------------------------------------------------------------- */
/*  MAIN SCREEN                                                          */
/* -------------------------------------------------------------------- */
@Composable
fun BusinessIntakeScreen(
    onBackClick: () -> Unit = {},
    onConfirmContinue: (String) -> Unit = {},
    onMicToggle: (isRecording: Boolean) -> Unit = {}
) {
    var selectedLanguage by remember { mutableStateOf(availableLanguages.first()) }
    var languageMenuExpanded by remember { mutableStateOf(false) }
    var isRecording by remember { mutableStateOf(false) }
    var businessIdeaText by remember { mutableStateOf("") }

    val context = LocalContext.current
    val audioRecorder = remember { AudioRecorderHelper(context) }

    val recordAudioLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission(),
        onResult = { isGranted ->
            if (isGranted) {
                isRecording = true
                audioRecorder.startRecording()
                onMicToggle(isRecording)
                Toast.makeText(context, "Recording started...", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(context, "Microphone permission denied", Toast.LENGTH_SHORT).show()
            }
        }
    )

    val canContinue = businessIdeaText.isNotBlank() || isRecording

    Scaffold(
        containerColor = KalpaScreenColors.ScreenBackgroundWhite,
        bottomBar = {
            ConfirmContinueBar(
                enabled = canContinue,
                onClick = { onConfirmContinue(businessIdeaText) }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
        ) {
            KalpaTopBar(
                onBackClick = onBackClick,
                stepText = "Page 1 of 14",
                trailingContent = {
                    LanguageSwitcher(
                        selectedLanguage = selectedLanguage,
                        languageMenuExpanded = languageMenuExpanded,
                        onLanguageClick = { languageMenuExpanded = true },
                        onLanguageDismiss = { languageMenuExpanded = false },
                        onLanguageSelected = {
                            selectedLanguage = it
                            languageMenuExpanded = false
                        }
                    )
                }
            )

            ProgressSection(percentComplete = 20)

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp)
            ) {
                Spacer(Modifier.height(20.dp))

                Text(
                    text = "Tell us about your business",
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 22.sp,
                    fontWeight = FontWeight.Bold,
                    lineHeight = 28.sp
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    text = "Speak or type your idea. Speak simply, like talking to a friend.",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 14.sp,
                    lineHeight = 20.sp
                )

                Spacer(Modifier.height(20.dp))

                SpeakCard(
                    isRecording = isRecording,
                    onMicClick = {
                        if (isRecording) {
                            isRecording = false
                            val filePath = audioRecorder.stopRecording()
                            onMicToggle(isRecording)
                            Toast.makeText(context, "Saved to $filePath", Toast.LENGTH_LONG).show()
                        } else {
                            if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                                isRecording = true
                                audioRecorder.startRecording()
                                onMicToggle(isRecording)
                                Toast.makeText(context, "Recording started...", Toast.LENGTH_SHORT).show()
                            } else {
                                recordAudioLauncher.launch(Manifest.permission.RECORD_AUDIO)
                            }
                        }
                    }
                )

                Spacer(Modifier.height(22.dp))

                OrDivider()

                Spacer(Modifier.height(18.dp))

                TypeIdeaField(
                    value = businessIdeaText,
                    onValueChange = { businessIdeaText = it },
                    onSubmit = { if (canContinue) onConfirmContinue(businessIdeaText) }
                )

                Spacer(Modifier.height(24.dp))
            }
        }
    }
}

/* -------------------------------------------------------------------- */
/*  LANGUAGE SWITCHER                                                    */
/* -------------------------------------------------------------------- */
@Composable
private fun LanguageSwitcher(
    selectedLanguage: String,
    languageMenuExpanded: Boolean,
    onLanguageClick: () -> Unit,
    onLanguageDismiss: () -> Unit,
    onLanguageSelected: (String) -> Unit
) {
    Box {
        Surface(
            shape = RoundedCornerShape(20.dp),
            color = KalpaScreenColors.PillGray,
            modifier = Modifier.clickable { onLanguageClick() }
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp)
            ) {
                Text(
                    text = selectedLanguage,
                    color = KalpaScreenColors.TextPrimary,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium
                )
                Spacer(Modifier.width(4.dp))
                Icon(
                    imageVector = Icons.Filled.ArrowDropDown,
                    contentDescription = "Change language",
                    tint = KalpaScreenColors.TextPrimary,
                    modifier = Modifier.size(18.dp)
                )
            }
        }
        DropdownMenu(
            expanded = languageMenuExpanded,
            onDismissRequest = onLanguageDismiss
        ) {
            availableLanguages.forEach { language ->
                DropdownMenuItem(
                    text = { Text(language) },
                    onClick = { onLanguageSelected(language) }
                )
            }
        }
    }
}

/* -------------------------------------------------------------------- */
/*  PROGRESS SECTION                                                     */
/* -------------------------------------------------------------------- */
@Composable
private fun ProgressSection(percentComplete: Int) {
    Column(modifier = Modifier.padding(horizontal = 20.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = "BUSINESS INTAKE",
                color = KalpaScreenColors.Orange,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 0.5.sp,
                modifier = Modifier.weight(1f).padding(end = 8.dp)
            )
            Text(
                text = "$percentComplete% Complete",
                color = KalpaScreenColors.TextMuted,
                fontSize = 12.sp
            )
        }
        Spacer(Modifier.height(8.dp))
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(4.dp)
                .clip(RoundedCornerShape(2.dp))
                .background(KalpaScreenColors.Divider)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth(percentComplete / 100f)
                    .fillMaxHeight()
                    .background(KalpaScreenColors.Orange)
            )
        }
    }
}

/* -------------------------------------------------------------------- */
/*  SPEAK CARD (mic button + example quote + supported languages)       */
/* -------------------------------------------------------------------- */
@Composable
private fun SpeakCard(
    isRecording: Boolean,
    onMicClick: () -> Unit
) {
    Surface(
        shape = RoundedCornerShape(20.dp),
        color = KalpaScreenColors.ScreenBackgroundWhite,
        border = androidx.compose.foundation.BorderStroke(1.dp, KalpaScreenColors.Divider),
        shadowElevation = 0.dp
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 26.dp, horizontal = 20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Outer soft ring + inner solid mic button
            Box(
                modifier = Modifier
                    .size(96.dp)
                    .clip(CircleShape)
                    .background(KalpaScreenColors.OrangeSoftMic),
                contentAlignment = Alignment.Center
            ) {
                Box(
                    modifier = Modifier
                        .size(68.dp)
                        .clip(CircleShape)
                        .background(if (isRecording) KalpaScreenColors.OrangeDark else KalpaScreenColors.Orange)
                        .clickable { onMicClick() },
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = if (isRecording) Icons.Filled.Stop else Icons.Filled.Mic,
                        contentDescription = if (isRecording) "Stop recording" else "Start recording",
                        tint = Color.White,
                        modifier = Modifier.size(30.dp)
                    )
                }
            }

            Spacer(Modifier.height(14.dp))

            Text(
                text = if (isRecording) "Listening…" else "Speak in your language",
                color = KalpaScreenColors.TextPrimary,
                fontSize = 15.sp,
                fontWeight = FontWeight.SemiBold
            )

            Spacer(Modifier.height(12.dp))

            Surface(
                shape = RoundedCornerShape(10.dp),
                color = KalpaScreenColors.QuoteBg
            ) {
                Text(
                    text = "\"I want to start a poultry farm in my village...\"",
                    color = KalpaScreenColors.TextSecondary,
                    fontSize = 12.5.sp,
                    fontStyle = FontStyle.Italic,
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 9.dp)
                )
            }

            Spacer(Modifier.height(12.dp))

            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "Hindi, Tamil, Telugu, Marathi, English",
                    color = KalpaScreenColors.LinkBlue,
                    fontSize = 12.5.sp,
                    fontWeight = FontWeight.Medium
                )
            }
        }
    }
}

/* -------------------------------------------------------------------- */
/*  "OR" DIVIDER                                                         */
/* -------------------------------------------------------------------- */
@Composable
private fun OrDivider() {
    Row(verticalAlignment = Alignment.CenterVertically) {
        HorizontalDivider(modifier = Modifier.weight(1f), color = KalpaScreenColors.Divider)
        Text(
            text = "OR TYPE YOUR IDEA",
            color = KalpaScreenColors.TextMuted,
            fontSize = 11.sp,
            fontWeight = FontWeight.SemiBold,
            letterSpacing = 0.5.sp,
            modifier = Modifier.padding(horizontal = 12.dp)
        )
        HorizontalDivider(modifier = Modifier.weight(1f), color = KalpaScreenColors.Divider)
    }
}

/* -------------------------------------------------------------------- */
/*  TEXT INPUT FIELD WITH SEND BUTTON                                    */
/* -------------------------------------------------------------------- */
@Composable
private fun TypeIdeaField(
    value: String,
    onValueChange: (String) -> Unit,
    onSubmit: () -> Unit
) {
    Surface(
        shape = RoundedCornerShape(28.dp),
        color = KalpaScreenColors.FieldGray
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(start = 18.dp, end = 6.dp, top = 6.dp, bottom = 6.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(modifier = Modifier.weight(1f), contentAlignment = Alignment.CenterStart) {
                if (value.isEmpty()) {
                    Text(
                        text = "Type your business idea here...",
                        color = KalpaScreenColors.TextMuted,
                        fontSize = 14.sp,
                        modifier = Modifier.padding(vertical = 10.dp)
                    )
                }
                BasicTextFieldCompat(
                    value = value,
                    onValueChange = onValueChange,
                    onSubmit = onSubmit
                )
            }

            Spacer(Modifier.width(8.dp))

            val sendEnabled = value.isNotBlank()
            Box(
                modifier = Modifier
                    .size(42.dp)
                    .clip(CircleShape)
                    .background(if (sendEnabled) KalpaScreenColors.Orange else KalpaScreenColors.Orange.copy(alpha = 0.5f))
                    .clickable(enabled = sendEnabled) { onSubmit() },
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Filled.ArrowUpward,
                    contentDescription = "Submit idea",
                    tint = Color.White,
                    modifier = Modifier.size(18.dp)
                )
            }
        }
    }
}

/**
 * Thin wrapper around BasicTextField so callers above don't need to manage
 * TextFieldValue / cursor position directly. Handles the "done"/"send" IME
 * action to trigger onSubmit, matching the up-arrow button behavior.
 */
@Composable
private fun BasicTextFieldCompat(
    value: String,
    onValueChange: (String) -> Unit,
    onSubmit: () -> Unit
) {
    androidx.compose.foundation.text.BasicTextField(
        value = value,
        onValueChange = onValueChange,
        singleLine = false,
        maxLines = 4,
        textStyle = androidx.compose.ui.text.TextStyle(
            color = KalpaScreenColors.TextPrimary,
            fontSize = 14.sp
        ),
        cursorBrush = androidx.compose.ui.graphics.SolidColor(KalpaScreenColors.Orange),
        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
        keyboardActions = androidx.compose.foundation.text.KeyboardActions(
            onSend = { onSubmit() }
        ),
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 10.dp)
    )
}

/* -------------------------------------------------------------------- */
/*  BOTTOM "CONFIRM & CONTINUE" BAR                                      */
/* -------------------------------------------------------------------- */
@Composable
private fun ConfirmContinueBar(
    enabled: Boolean,
    onClick: () -> Unit
) {
    Surface(color = KalpaScreenColors.ScreenBackgroundWhite) {
        Column(modifier = Modifier.padding(20.dp)) {
            Button(
                onClick = onClick,
                enabled = enabled,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(54.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = KalpaScreenColors.Orange,
                    disabledContainerColor = KalpaScreenColors.Orange.copy(alpha = 0.45f)
                )
            ) {
                Text(
                    text = "Confirm & Continue",
                    color = Color.White,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.SemiBold
                )
                Spacer(Modifier.width(8.dp))
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.ArrowForward,
                    contentDescription = null,
                    tint = Color.White,
                    modifier = Modifier.size(18.dp)
                )
            }
        }
    }
}

/* -------------------------------------------------------------------- */
/*  PREVIEW                                                              */
/* -------------------------------------------------------------------- */
@androidx.compose.ui.tooling.preview.Preview(showBackground = true, widthDp = 390, heightDp = 844)
@Composable
private fun BusinessIntakeScreenPreview() {
    MaterialTheme {
        BusinessIntakeScreen()
    }
}