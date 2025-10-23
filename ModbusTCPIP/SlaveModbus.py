import asyncio
import RPi.GPIO as GPIO
from pymodbus.server.async_io import ModbusTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification

# GPIO setup
output1 = 23  # GPIO pin number
GPIO.setmode(GPIO.BCM)
GPIO.setup(output1, GPIO.OUT)
GPIO.output(output1, GPIO.LOW)

# Modbus context (coils for on/off control)
store = ModbusSlaveContext(
    co=ModbusSequentialDataBlock(0, [False]*10), 
    di=None, hr=None, ir=None
)
context = ModbusServerContext(slaves=store, single=True)

# Device identity (optional)
identity = ModbusDeviceIdentification()
identity.VendorName = 'IONI PI'
identity.ProductCode = 'RPI'
identity.VendorUrl = 'http://example.com'
identity.ModelName = 'IONI Modbus GPIO Server'
identity.MajorMinorRevision = '1.0'

# Background task to monitor coil changes and update GPIO
async def monitor_coils():
    while True:
        coil_values = context[0].getValues(1, 0, count=1)  # Get coil at address 0
        GPIO.output(output1, GPIO.HIGH if coil_values[0] else GPIO.LOW)
        await asyncio.sleep(0.1)  # Poll every 100 ms

# Start Modbus TCP server
async def run_server():
    server = ModbusTcpServer(context, identity=identity, address=("0.0.0.0", 1502))
    print("IONI PI Modbus TCP server started on port 1502")
    await asyncio.gather(server.serve_forever(), monitor_coils())

if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("Server stopped and GPIO cleaned up.")
