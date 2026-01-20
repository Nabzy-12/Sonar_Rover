const RADIO_GROUP = 42
radio.setGroup(RADIO_GROUP)

function clamp(n: number, lo: number, hi: number): number {
    return Math.max(lo, Math.min(hi, n))
}

function sendTank(left: number, right: number) {
    radio.sendString("T:" + left + "," + right)
}

input.onButtonPressed(Button.A, function () {
    radio.sendString("STOP")
})

input.onButtonPressed(Button.B, function () {
    // Cycle rover mode
    radio.sendString("MANUAL")
    basic.pause(80)
    radio.sendString("AVOID")
    basic.pause(80)
    radio.sendString("FOLLOW")
    basic.pause(80)
    radio.sendString("SCAN")
})

basic.forever(function () {
    // Pitch: forward/back, Roll: steering
    const pitch = input.rotation(Rotation.Pitch) // -90..90 approx
    const roll = input.rotation(Rotation.Roll)

    const fwd = clamp(Math.floor(-pitch / 2), -45, 45)
    const steer = clamp(Math.floor(roll / 3), -30, 30)

    const left = clamp(fwd - steer, -70, 70)
    const right = clamp(fwd + steer, -70, 70)

    sendTank(left, right)
    basic.pause(80)
})
