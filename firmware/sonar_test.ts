// MINIMAL SONAR TEST - Flash this first to verify hardware works
// Shows distance on LED display AND sends to serial

// Sonar pins for MiniBit (directly access since we're testing)
const SONAR_TRIG = DigitalPin.P13
const SONAR_ECHO = DigitalPin.P13

basic.showIcon(IconNames.Heart)
basic.pause(500)

serial.redirectToUSB()
serial.setBaudRate(BaudRate.BaudRate115200)
serial.writeLine("BOOT:sonar_test")

basic.forever(function () {
    // Read sonar using MiniBit's built-in function
    let dist = minibit.sonar(mbPingUnit.Centimeters)
    
    // Show on LED (0-99 or "X" if out of range)
    if (dist > 0 && dist < 100) {
        basic.showNumber(dist)
    } else if (dist >= 100 && dist < 200) {
        basic.showString("" + Math.floor(dist / 10))
    } else {
        basic.showIcon(IconNames.No)
    }
    
    // Send to serial as JSON
    let heading = input.compassHeading()
    serial.writeLine("{\"dist_cm\":" + dist + ",\"heading_deg\":" + heading + "}")
    
    // LED color based on distance
    if (dist > 0 && dist < 20) {
        minibit.setLedColor(mbColors.Red)
    } else if (dist < 50) {
        minibit.setLedColor(mbColors.Yellow)
    } else {
        minibit.setLedColor(mbColors.Green)
    }
    
    basic.pause(200)
})
