/**
 * PC-CONTROLLED ROVER - ANGLE TRACKED ON-BOARD
 * =============================================
 * Firmware tracks its own angle - sends it to PC
 * No guessing needed!
 * 
 * Commands: F, B, L, R, SF, ST, X
 * 
 * MakeCode: https://makecode.microbit.org
 * Extension: github:4tronix/MiniBit
 */

let dist = 0
let angle = 0        // Tracked angle (degrees, 0 = starting direction)
let state = "STOP"
let driving = 0
let turning = 0
let lastTime = 0

const MOVE_SPEED = 40
const TURN_SPEED = 30
const DEGREES_PER_MS = 0.12  // Calibrate this! Degrees turned per millisecond

// Startup
serial.setBaudRate(BaudRate.BaudRate115200)
basic.showIcon(IconNames.Square)
minibit.setLedColor(0x0000FF)
lastTime = input.runningTime()

// Button A: Emergency Stop
input.onButtonPressed(Button.A, function () {
    driving = 0
    turning = 0
    minibit.stop(mbStopMode.Brake)
    state = "STOP"
    minibit.setLedColor(0x0000FF)
})

// Button B: Reset angle to 0
input.onButtonPressed(Button.B, function () {
    angle = 0
    basic.showIcon(IconNames.Yes)
    basic.pause(200)
    basic.showIcon(IconNames.Square)
})

function applyMotors() {
    // Simple approach: prioritize drive over turn
    if (driving == 0 && turning == 0) {
        state = "STOP"
        minibit.setLedColor(0x0000FF)
        minibit.stop(mbStopMode.Brake)
    } else if (driving != 0) {
        // Driving (with optional turn bias)
        if (driving == 1) {
            state = "FWD"
            minibit.setLedColor(0x00FF00)
            if (turning == 1) {
                // Forward + left: left slower
                minibit.move(mbMotor.Left, mbDirection.Forward, MOVE_SPEED - TURN_SPEED)
                minibit.move(mbMotor.Right, mbDirection.Forward, MOVE_SPEED)
                state = "FWD_L"
            } else if (turning == -1) {
                // Forward + right: right slower
                minibit.move(mbMotor.Left, mbDirection.Forward, MOVE_SPEED)
                minibit.move(mbMotor.Right, mbDirection.Forward, MOVE_SPEED - TURN_SPEED)
                state = "FWD_R"
            } else {
                minibit.go(mbDirection.Forward, MOVE_SPEED)
            }
        } else {
            state = "REV"
            minibit.setLedColor(0xFF8800)
            if (turning == 1) {
                minibit.move(mbMotor.Left, mbDirection.Reverse, MOVE_SPEED - TURN_SPEED)
                minibit.move(mbMotor.Right, mbDirection.Reverse, MOVE_SPEED)
                state = "REV_L"
            } else if (turning == -1) {
                minibit.move(mbMotor.Left, mbDirection.Reverse, MOVE_SPEED)
                minibit.move(mbMotor.Right, mbDirection.Reverse, MOVE_SPEED - TURN_SPEED)
                state = "REV_R"
            } else {
                minibit.go(mbDirection.Reverse, MOVE_SPEED)
            }
        }
    } else {
        // Turn in place only
        minibit.setLedColor(0xFF00FF)
        if (turning == 1) {
            state = "LEFT"
            minibit.rotate(mbRobotDirection.Left, TURN_SPEED)
        } else {
            state = "RIGHT"
            minibit.rotate(mbRobotDirection.Right, TURN_SPEED)
        }
    }
}

// Serial command receiver
serial.onDataReceived(serial.delimiters(Delimiters.NewLine), function () {
    let cmd = serial.readUntil(serial.delimiters(Delimiters.NewLine))
    
    if (cmd == "F") {
        driving = 1
    } else if (cmd == "B") {
        driving = -1
    } else if (cmd == "SF") {
        driving = 0  // Stop forward/back axis only
    } else if (cmd == "L") {
        turning = 1
    } else if (cmd == "R") {
        turning = -1
    } else if (cmd == "ST") {
        turning = 0  // Stop turn axis only
    } else if (cmd == "X") {
        driving = 0
        turning = 0
    }
    
    applyMotors()
})

// Main loop - track angle + send telemetry
basic.forever(function () {
    let now = input.runningTime()
    let dt = now - lastTime
    lastTime = now
    
    // Update angle based on turning
    if (turning == 1) {
        angle = angle + (dt * DEGREES_PER_MS)
    } else if (turning == -1) {
        angle = angle - (dt * DEGREES_PER_MS)
    }
    
    // Keep angle in 0-360
    while (angle < 0) { angle = angle + 360 }
    while (angle >= 360) { angle = angle - 360 }
    
    dist = minibit.sonar(mbPingUnit.Centimeters)
    serial.writeLine('{"d":' + dist + ',"a":' + Math.round(angle) + ',"s":"' + state + '"}')
    basic.pause(25)
})
