/*
 * Código parcial da implementação do controle
 * de LEDS via Json (futuramente controlar por IFTTT)
 * pino 2 3 e 4 PWM analogicos RGB
 * ps: codigo com delay de +/- 13 segundos por requisição HTTP WTF??? provavelmente codigo
 * em alguma library (httpclient.h???)
*/
 
int red; //variável temporária usada na conversão de HEX para Decimal cor vermelho
int green; //variável temporária usada na conversão de HEX para Decimal cor verde
int blue; //variável temporária usada na conversão de HEX para Decimal cor azul
 
int redOld;
int greenOld;
int blueOld;
 
#include <SPI.h>
#include <WiFi101.h>
#include <ArduinoJson.h>
#include "arduino_secrets.h" 
 
//nome da rede e senha definidos no arquivo arduino_secrets.h
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;
 
char color[] = {0,0,0,0,0,0};
 
//variável para status do wifi
int status = WL_IDLE_STATUS;
 
//cria um "objeto" wifi
WiFiClient client;
//define servidor e porta para a conexão http com as cores que vão para o LED
//HttpClient clienthttp = HttpClient(client, "rianfc.pythonanywhere.com", 80);
 
//inicialização do arduino MKR1000
void setup() {
  Serial.begin(9600);
  //testa os 2 cananis de cores da fitra de led
  //R -> B -> G -> W
  setColor(0, 0, 0);
  delay(500);
  setColor(255, 0, 0);
  delay(500);
  setColor(0, 255, 0);
  delay(500);
  setColor(0, 0, 255);
  delay(500);
  setColor(255, 255, 255);
  delay(500);
  setColor(0, 0, 0);
 
  // Checar se existe shield wifi no arduino
  if (WiFi.status() == WL_NO_SHIELD) {
    Serial.println("WiFi shield not present");
    // don't continue:
    while (true);
  }
 
  // iniciar conexão WIFI
  while (status != WL_CONNECTED) {
    // Conecta numa rede WPA/WPA2
    status = WiFi.begin(ssid, pass);
 
    // espera 10 segundos para a conexão wifi
    delay(10000);
  }
 
  printWiFiStatus();
 
}//final setup
 
//seta os valores passados nas portas PWM
void setColor(int R, int G, int B) {
  analogWrite(3, R);
  analogWrite(4, G);
  analogWrite(5, B);
  redOld = R;
  greenOld = G;
  blueOld = B;
}
 
//transforma um array de char com valoras em HEX para INT
void getColor(const char valores[]) {
  //separação do vetor grande em 3 menores
  char tempr[2] = {valores[0], valores[1]};
  char tempg[2] = {valores[2], valores[3]};
  char tempb[2] = {valores[4], valores[5]};
  //conversão do svetores menorem para decimal
  red = (int) strtol(tempr, 0, 16);
  green = (int) strtol(tempg, 0, 16);
  blue = (int) strtol(tempb, 0, 16);
}
 
void loop() {
  //pega cor atual da página do Rian
  getColorWeb();
  //separa os 3 canais de cores R G B
  getColor(color);
  Serial.println(color);
  //Seta as cores no led se os valores forem diferentes do atual (evita flicker)
  if(red == redOld & green == greenOld && blue == blueOld){
    //do nothing
  }else{
    setColor(red, green, blue);
  }
 
  //espera 1s pra pegar a proxima cor
  delay(1000);
}
 
//printa o status da conexão wifi
void printWiFiStatus() {
  // printa o SSID da rede
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());
 
  // printa o ip
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);
 
  // printa força do sinal
  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}
 
//trabalho sujo http e json
void getColorWeb(){
  //conecta na pagina do Rian
  if (!client.connect("rianfc.pythonanywhere.com", 80)) {
    Serial.println(F("Falha ao se conectar"));
    return;
  }
  //faz requisição http do json
  client.println(F("GET /get HTTP/1.0"));
  client.println(F("Host: rianfc.pythonanywhere.com"));
  client.println(F("Connection: close"));
  if (client.println() == 0) {
    Serial.println(F("Falha ao enviar requisicao"));
    return;
  }
 
  //checa se o http retornou 200 OK, caso contrário imprime a resposta na serial
  char status[32] = {0};
  client.readBytesUntil('\r', status, sizeof(status));
  if (strcmp(status, "HTTP/1.1 200 OK") != 0) {
    Serial.print(F("Resposta inesperada: "));
    Serial.println(status);
    return;
  }
 
  //separa o header da resposta http
  char endOfHeaders[] = "\r\n\r\n";
  if (!client.find(endOfHeaders)) {
    Serial.println(F("Resposta inválida"));
    return;
  }
 
  //Criando Json
  // Use arduinojson.org/v6/assistant to compute the capacity.
  const size_t capacity = JSON_OBJECT_SIZE(2) + 20;
  DynamicJsonDocument doc(capacity);
 
  //extraindo campos da resposta Json
  DeserializationError error = deserializeJson(doc, client);
  if (error) {
    Serial.print(F("deserializeJson() falhou: "));
    Serial.println(error.c_str());
    return;
  }
  const char* temp = doc["color"];
 
  //Desconecta
  client.stop();
 
  color[0] = temp[0];
  color[1] = temp[1];
  color[2] = temp[2];
  color[3] = temp[3];
  color[4] = temp[4];
  color[5] = temp[5];
}
