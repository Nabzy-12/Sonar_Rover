// Rover firmware entrypoint.
//
// This is kept at repo root so you can import the GitHub repo directly into
// https://makecode.microbit.org/.
//
// The “real” source is maintained in firmware/rover/main.ts. If you change one,
// copy the same changes to the other.

enum RoverMode {
    Manual = 0,
    Avoid = 1,
    Follow = 2,
    Scan = 3,
}

// --- Tuning knobs ---
const RADIO_GROUP = 42
const BAUD = BaudRate.BaudRate115200

const SAFE_CM = 18
const FOLLOW_TARGET_CM = 25
const FOLLOW_TOL_CM = 4

const DRIVE_SPEED = 55
const TURN_SPEED = 55

// Sonar smoothing
const SONAR_SAMPLES = 3

// Prefer compass heading when available
const USE_COMPASS = true

let mode = RoverMode.Avoid
let scanning = false
let lastManualL = 0
let lastManualR = 0

function clamp(n: number, lo: number, hi: number): number {
    return Math.max(lo, Math.min(hi, n))
}

function driveMotor(which: mbMotor, speed: number) {
    // speed in [-100..100]
    const s = clamp(speed, -100, 100)
    if (s === 0) {
        minibit.move(which, mbDirection.Forward, 0)
        return
    }

    const dir = s > 0 ? mbDirection.Forward : mbDirection.Reverse
    minibit.move(which, dir, Math.abs(s))
}

function driveTank(left: number, right: number) {
    driveMotor(mbMotor.Left, left)
    driveMotor(mbMotor.Right, right)
}

function stopBrake() {
    minibit.stop(mbStopMode.Brake)
}

function readSonarCm(): number {
    let total = 0
    let count = 0
    for (let i = 0; i < SONAR_SAMPLES; i++) {
        const d = minibit.sonar(mbPingUnit.Centimeters)
        if (d > 0) {
            total += d
            count++
        }
        basic.pause(10)
    }
    if (count === 0) return 0
    return Math.floor(total / count)
}

function getHeadingDeg(): number {
    if (!USE_COMPASS) return -1
    return input.compassHeading()
}

function modeName(m: RoverMode): string {
    switch (m) {
        case RoverMode.Manual: return "manual"
        case RoverMode.Avoid: return "avoid"
        case RoverMode.Follow: return "follow"
        case RoverMode.Scan: return "scan"
        default: return "unknown"
    }
}

function emitTelemetry(distCm: number, note: string) {
    const heading = getHeadingDeg()
    const msg = "{\"t\":" + control.millis() +
        ",\"mode\":\"" + modeName(mode) + "\"" +
        ",\"dist_cm\":" + distCm +
        ",\"heading_deg\":" + heading +
        ",\"note\":\"" + note + "\"}"
    serial.writeLine(msg)
}

function setMode(newMode: RoverMode) {
    if (mode === newMode) return

    if (mode === RoverMode.Scan) {
        scanning = false
        stopBrake()
    }

    mode = newMode
    emitTelemetry(readSonarCm(), "mode")

    if (mode === RoverMode.Scan) {
        startScan()
    }
}

function parseTank(cmd: string) {
    // Format: T:<left>,<right>
    const body = cmd.substr(2)
    const parts = body.split(",")
    if (parts.length < 2) return

    const l = parseInt(parts[0])
    const r = parseInt(parts[1])
    if (isNaN(l) || isNaN(r)) return

    lastManualL = clamp(l, -100, 100)
    lastManualR = clamp(r, -100, 100)
    setMode(RoverMode.Manual)
    driveTank(lastManualL, lastManualR)
    emitTelemetry(readSonarCm(), "tank")
}

function parseCommand(raw: string) {
    let cmd = raw.trim()
    if (!cmd) return

    cmd = cmd.toUpperCase()

    if (cmd === "MANUAL") { setMode(RoverMode.Manual); return }
    if (cmd === "AVOID") { setMode(RoverMode.Avoid); return }
    if (cmd === "FOLLOW") { setMode(RoverMode.Follow); return }
    if (cmd === "SCAN") { setMode(RoverMode.Scan); return }

    if (cmd === "S" || cmd === "STOP") {
        lastManualL = 0
        lastManualR = 0
        setMode(RoverMode.Manual)
        stopBrake()
        emitTelemetry(readSonarCm(), "stop")
        return
    }

    if (cmd.indexOf("T:") === 0) {
        parseTank(cmd)
        return
    }

    if (cmd === "F") {
        setMode(RoverMode.Manual)
        lastManualL = DRIVE_SPEED
        lastManualR = DRIVE_SPEED
        driveTank(lastManualL, lastManualR)
        emitTelemetry(readSonarCm(), "F")
        return
    }
    if (cmd === "B") {
        setMode(RoverMode.Manual)
        lastManualL = -DRIVE_SPEED
        lastManualR = -DRIVE_SPEED
        driveTank(lastManualL, lastManualR)
        emitTelemetry(readSonarCm(), "B")
        return
    }
    if (cmd === "L") {
        setMode(RoverMode.Manual)
        lastManualL = -TURN_SPEED
        lastManualR = TURN_SPEED
        driveTank(lastManualL, lastManualR)
        emitTelemetry(readSonarCm(), "L")
        return
    }
    if (cmd === "R") {
        setMode(RoverMode.Manual)
        lastManualL = TURN_SPEED
        lastManualR = -TURN_SPEED
        driveTank(lastManualL, lastManualR)
        emitTelemetry(readSonarCm(), "R")
        return
    }
}

function startScan() {
    if (scanning) return
    scanning = true

    control.inBackground(function () {
        stopBrake()
        basic.pause(200)
        emitTelemetry(readSonarCm(), "scan_start")

        while (scanning) {
            const d = readSonarCm()
            emitTelemetry(d, "scan")

            minibit.rotatems(mbRobotDirection.Left, 35, 120)
            basic.pause(30)

            if (d > 0 && d < SAFE_CM) {
                minibit.goms(mbDirection.Reverse, 35, 200)
                stopBrake()
                basic.pause(100)
            }
        }

        stopBrake()
        emitTelemetry(readSonarCm(), "scan_stop")
    })
}

serial.redirectToUSB()
serial.setBaudRate(BAUD)
radio.setGroup(RADIO_GROUP)

serial.onDataReceived(serial.delimiters(Delimiters.NewLine), function () {
    const line = serial.readLine()
    parseCommand(line)
})

radio.onReceivedString(function (receivedString: string) {
    parseCommand(receivedString)
})

input.onButtonPressed(Button.A, function () {
    if (mode === RoverMode.Manual) setMode(RoverMode.Avoid)
    else if (mode === RoverMode.Avoid) setMode(RoverMode.Follow)
    else if (mode === RoverMode.Follow) setMode(RoverMode.Scan)
    else setMode(RoverMode.Manual)
})

input.onButtonPressed(Button.B, function () {
    stopBrake()
    emitTelemetry(readSonarCm(), "btn_stop")
})

input.onButtonPressed(Button.AB, function () {
    if (mode === RoverMode.Scan) setMode(RoverMode.Avoid)
    else setMode(RoverMode.Scan)
})

minibit.setLedColor(mbColors.Blue)
emitTelemetry(readSonarCm(), "boot")

basic.forever(function () {
    if (mode === RoverMode.Manual) {
        basic.pause(50)
        return
    }

    if (mode === RoverMode.Scan) {
        basic.pause(100)
        return
    }

    const dist = readSonarCm()
    emitTelemetry(dist, "tick")

    if (mode === RoverMode.Avoid) {
        if (dist > 0 && dist < SAFE_CM) {
            minibit.setLedColor(mbColors.Red)
            stopBrake()
            basic.pause(100)

            minibit.goms(mbDirection.Reverse, 45, 250)
            stopBrake()
            basic.pause(50)

            const dir = Math.randomRange(0, 1) === 0 ? mbRobotDirection.Left : mbRobotDirection.Right
            minibit.rotatems(dir, 55, 350)
            stopBrake()
            minibit.setLedColor(mbColors.Blue)
            basic.pause(50)
        } else {
            minibit.go(mbDirection.Forward, DRIVE_SPEED)
        }
    } else if (mode === RoverMode.Follow) {
        minibit.setLedColor(mbColors.Green)

        if (dist === 0) {
            minibit.go(mbDirection.Forward, 30)
        } else {
            const err = dist - FOLLOW_TARGET_CM
            if (Math.abs(err) <= FOLLOW_TOL_CM) {
                stopBrake()
            } else {
                const sp = clamp(Math.abs(err) * 3, 20, 70)
                if (err > 0) minibit.go(mbDirection.Forward, sp)
                else minibit.go(mbDirection.Reverse, sp)
            }
        }
    }

    basic.pause(120)
})
