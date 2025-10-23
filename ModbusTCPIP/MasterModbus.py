import sounddevice as sd
import queue
import vosk
import json
from pymodbus.client import ModbusTcpClient

# VOSK model path (adjust this to your local system)
model = vosk.Model(r"C:\vosk-model-small-en-us-0.15")
q = queue.Queue()

# Modbus client config
MODBUS_SERVER_IP = "192.168.200.193"  # Raspberry Pi IP
MODBUS_PORT = 1502
client = ModbusTcpClient(MODBUS_SERVER_IP, port=MODBUS_PORT)

# Audio input callback
def callback(indata, frames, time, status):
    q.put(bytes(indata))

# Send Modbus command based on voice command
def send_modbus_command(command):
    if command == "start":
        print("Command: START")
        result = client.write_coil(0, True)  # Coil 0 ON
        if result.isError():
            print("Failed to send 'start'")
        else:
            print("Motor set to ON")

    elif command == "stop":
        print("Command: STOP")
        result = client.write_coil(0, False)  # Coil 0 OFF
        if result.isError():
            print("Failed to send 'stop'")
        else:
            print("Motor set to OFF")

# Main voice recognition loop
def main():
    if client.connect():
        print(f"Connected to Modbus server at {MODBUS_SERVER_IP}:{MODBUS_PORT}")
    else:
        print(f"Failed to connect to Modbus server at {MODBUS_SERVER_IP}:{MODBUS_PORT}")
        return

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        rec = vosk.KaldiRecognizer(model, 16000)
        print("Say 'start' or 'stop'...")

        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                command = result.get("text", "")
                if "start" in command:
                    send_modbus_command("start")
                elif "stop" in command:
                    send_modbus_command("stop")
                else:
                    print(f"Unrecognized: {command}")
            # Optional: print partial results
            # else:
            #     print(f"Partial: {rec.PartialResult()}")

    client.close()

if __name__ == "__main__":
    main()
