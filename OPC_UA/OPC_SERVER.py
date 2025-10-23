import asyncio
import sounddevice as sd
import queue
import vosk
import json
from word2number import w2n
from asyncua import Client, ua

# OPC UA settings
OPC_SERVER_URL = "opc.tcp://localhost:51210/UA/SampleServer"
NODE_ID = "ns=3;s=AASROOT.ExampleMotor.OperationalData.RotationSpeed.Value"

# Load VOSK model (update path to your system)
model = vosk.Model(r"C:\vosk-model-small-en-us-0.15")
q = queue.Queue()

# Audio callback function
def callback(indata, frames, time, status):
    q.put(bytes(indata))

# Write to OPC UA and verify by reading back
async def write_and_verify_speed(value):
    print(f"Attempting to set speed to {value} RPM...")
    try:
        async with Client(OPC_SERVER_URL) as client:
            node = client.get_node(NODE_ID)

            # Write as Int64
            ua_value = ua.Variant(value, ua.VariantType.Int64)
            await node.write_value(ua_value)

            # Read back the value
            confirmed = await node.read_value()
            if confirmed == value:
                print(f" Success: set and verified as {confirmed} RPM.")
            else:
                print(f"⚠ Mismatch: Wrote {value}, but read back {confirmed}.")
    except Exception as e:
        print(f" OPC UA error: {e}")

# Handle recognized speech command
async def handle_command(text):
    print(f"You said: '{text}'")
    if "speed to" in text or "speed" in text:
        try:
            spoken = text.replace("speed to", "").replace("speed", "").strip()
            speed = w2n.word_to_num(spoken)
            await write_and_verify_speed(speed)
        except Exception as e:
            print(f" Could not interpret speed from speech: {e}")
    else:
        print(" Say: 'speed to <number>'")

# Main voice recognition loop
def main():
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        rec = vosk.KaldiRecognizer(model, 16000)
        print(" Say something like 'speed to three thousand'...")

        loop = asyncio.get_event_loop()
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                if text:
                    loop.run_until_complete(handle_command(text))

if __name__ == "__main__":
    main()
