/*********************************************************************************************************
This code reads the humidity and temperature value from DHT11 sensor (which is connected to pin 8),
and sends this reading via CAN Bus protocol with module MCP2515 (CS connected to pin 10).
*********************************************************************************************************/
#include <mcp_can.h>
#include <SPI.h>
#include <DHT.h>       

#define DHTPIN 8              // Set DHT sensor to pin 8
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);     //initilize object dht for class DHT with DHT pin with STM32 and DHT type as DHT11
MCP_CAN CAN0(10);             // Set CS to pin 10
byte data[8];

void setup()
{
  Serial.begin(115200);
  SPI.begin();               //Begins SPI communication
  dht.begin();               //Begins to read temperature & humidity sesnor value

  // Initialize MCP2515 running at 16MHz with a baudrate of 500kb/s and the masks and filters disabled.
  if(CAN0.begin(MCP_ANY, CAN_500KBPS, MCP_16MHZ) == CAN_OK) Serial.println("MCP2515 Initialized Successfully!");
  else Serial.println("Error Initializing MCP2515...");
  CAN0.setMode(MCP_NORMAL);   // Change to normal mode to allow messages to be transmitted
}


void loop()
{
  float h = dht.readHumidity();       //Gets Humidity value
  float t = dht.readTemperature();    //Gets Temperature value
  
  // Convert float values to bytes
  byte* hBytes = (byte*)&h;
  byte* tBytes = (byte*)&t;

  // Assign the bytes to the data array
  for (int i = 0; i < 4; i++) {
    data[i] = hBytes[i];
    data[i + 4] = tBytes[i];
  }

  // send data:  ID = 0x100, Standard CAN Frame, Data length = 8 bytes, 'data' = array of data bytes to send
  byte sndStat = CAN0.sendMsgBuf(0x100, 0, 8, data);
  if(sndStat == CAN_OK){
    Serial.println("Message Sent Successfully!");
  } else {
    Serial.println("Error Sending Message...");
  }
  delay(1000);   // send data per 1000ms
}

/*********************************************************************************************************
  END FILE
*********************************************************************************************************/