/**
 * FAST SONAR SCANNER
 * ===================
 * Optimized for rapid scanning and visualization.
 * Sends distance readings as fast as possible.
 * 
 * Import this into MakeCode: https://makecode.microbit.org
 * Add extension: github:4tronix/MiniBit
 */

// Fast continuous scanning
basic.forever(function () {
    // Read sonar
    let dist = minibit.sonar(mbPingUnit.Centimeters)
    
    // Send via serial immediately
    serial.writeLine('{"dist_cm":' + dist + '}')
    
    // Quick color feedback on LEDs
    if (dist < 20) {
        minibit.setLedColor(0xFF0000)  // Red - very close
    } else if (dist < 50) {
        minibit.setLedColor(0xFF4400)  // Orange
    } else if (dist < 100) {
        minibit.setLedColor(0xFFFF00)  // Yellow
    } else if (dist < 150) {
        minibit.setLedColor(0x00FF00)  // Green
    } else {
        minibit.setLedColor(0x0088FF)  // Blue - far
    }
    
    // Minimal pause - just enough for sonar to work
    basic.pause(50)  // 50ms = ~20 readings/sec!
})

// Startup indication
basic.showIcon(IconNames.Target)
basic.pause(500)
basic.clearScreen()
serial.setBaudRate(BaudRate.BaudRate115200)
