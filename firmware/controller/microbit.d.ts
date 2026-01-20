// Type stubs for micro:bit MakeCode APIs (for VS Code IntelliSense only).
// These do nothing at runtime — MakeCode provides the real implementations.

declare namespace basic {
    function pause(ms: number): void
    function forever(body: () => void): void
    function showNumber(n: number): void
    function showString(s: string): void
    function showIcon(icon: IconNames): void
    function clearScreen(): void
}

declare namespace input {
    function onButtonPressed(button: Button, body: () => void): void
    function compassHeading(): number
    function rotation(kind: Rotation): number
    function temperature(): number
    function lightLevel(): number
    function acceleration(dimension: Dimension): number
}

declare namespace serial {
    function writeLine(text: string): void
    function readLine(): string
    function redirectToUSB(): void
    function setBaudRate(rate: BaudRate): void
    function onDataReceived(delimiters: string, body: () => void): void
    function readUntil(delimiter: string): string
    function writeString(text: string): void
    function writeNumber(value: number): void
    function writeValue(name: string, value: number): void
    function readString(): string
    function delimiters(del: Delimiters): string
}

declare namespace radio {
    function setGroup(id: number): void
    function sendString(msg: string): void
    function sendNumber(value: number): void
    function onReceivedString(cb: (receivedString: string) => void): void
    function onReceivedNumber(cb: (receivedNumber: number) => void): void
}

declare namespace control {
    function millis(): number
    function inBackground(body: () => void): void
    function reset(): void
    function waitMicros(micros: number): void
}

declare namespace pins {
    function digitalReadPin(name: DigitalPin): number
    function digitalWritePin(name: DigitalPin, value: number): void
    function analogReadPin(name: AnalogPin): number
    function analogWritePin(name: AnalogPin, value: number): void
    function servoWritePin(name: AnalogPin, value: number): void
    function i2cReadNumber(address: number, format: NumberFormat, repeated?: boolean): number
    function i2cWriteNumber(address: number, value: number, format: NumberFormat, repeated?: boolean): void
    function spiWrite(value: number): number
    function map(value: number, fromLow: number, fromHigh: number, toLow: number, toHigh: number): number
    function pulseIn(name: DigitalPin, value: PulseValue, maxDuration?: number): number
}

// MakeCode extends Math with these (can't redeclare namespace, so declare as interface merge)
interface Math {
    idiv(a: number, b: number): number
    imul(a: number, b: number): number
    constrain(value: number, low: number, high: number): number
    randomRange(min: number, max: number): number
}

// Enums
declare const enum Button { A, B, AB }
declare const enum Rotation { Pitch, Roll }
declare const enum Dimension { X, Y, Z, Strength }
declare const enum BaudRate {
    BaudRate115200 = 115200,
    BaudRate57600 = 57600,
    BaudRate38400 = 38400,
    BaudRate31250 = 31250,
    BaudRate28800 = 28800,
    BaudRate19200 = 19200,
    BaudRate14400 = 14400,
    BaudRate9600 = 9600,
    BaudRate4800 = 4800,
    BaudRate2400 = 2400,
    BaudRate1200 = 1200
}
declare const enum Delimiters { NewLine, Comma, Dollar, Colon, Fullstop, Hash, Tab, Pipe, SemiColon, Space }
declare const enum DigitalPin { P0, P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11, P12, P13, P14, P15, P16, P19, P20 }
declare const enum AnalogPin { P0, P1, P2, P3, P4, P10 }
declare const enum PulseValue { High, Low }
declare const enum NumberFormat { Int8LE, UInt8LE, Int16LE, UInt16LE, Int32LE, UInt32LE, Float32LE, Float64LE }
declare const enum IconNames { Heart, SmallHeart, Yes, No, Happy, Sad, Confused, Angry, Asleep, Surprised, Silly, Fabulous, Meh, TShirt, Rollerskate, Duck, House, Tortoise, Butterfly, StickFigure, Ghost, Sword, Giraffe, Skull, Umbrella, Snake, Rabbit, Cow, QuarterNote, EigthNote, Pitchfork, Target, Triangle, LeftTriangle, Chessboard, Diamond, SmallDiamond, Square, SmallSquare, Scissors }

// 4tronix MiniBit types
declare const enum mbMotor { Left, Right, Both }
declare const enum mbDirection { Forward, Reverse }
declare const enum mbStopMode { Coast, Brake }
declare const enum mbRobotDirection { Left, Right }
declare const enum mbPingUnit { Centimeters, Inches, MicroSeconds }
declare const enum mbColors { Red = 0xff0000, Orange = 0xffa500, Yellow = 0xffff00, Green = 0x00ff00, Blue = 0x0000ff, Indigo = 0x4b0082, Violet = 0x8a2be2, Purple = 0xff00ff, White = 0xffffff, Black = 0x000000 }
declare const enum mbMode { Auto, Manual }

declare namespace minibit {
    function go(direction: mbDirection, speed: number): void
    function goms(direction: mbDirection, speed: number, duration: number): void
    function move(motor: mbMotor, direction: mbDirection, speed: number): void
    function rotate(direction: mbRobotDirection, speed: number): void
    function rotatems(direction: mbRobotDirection, speed: number, duration: number): void
    function stop(mode: mbStopMode): void
    function sonar(unit: mbPingUnit): number
    function setLedColor(color: number): void
    function ledClear(): void
    function setPixelColor(pixel: number, color: number): void
    function ledRainbow(): void
    function ledRotate(): void
    function ledShift(): void
    function setUpdateMode(mode: mbMode): void
    function ledBrightness(brightness: number): void
    function convertRGB(r: number, g: number, b: number): number
    function mbBias(direction: mbRobotDirection, bias: number): void
}
