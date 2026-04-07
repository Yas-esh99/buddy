#include "audio_capture.h"
#include "network.h"
#include "ring_buf.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"

//ffplay -protocol_whitelist file,udp,rtp -i audio.sdp

void app_main() {

  ring_buffer_init();

  i2s_init();
  wifi_init();

  xTaskCreate(i2s_task,"i2s task",4096,NULL,6,NULL);
  xTaskCreate(wifi_task,"wifi task",4096,NULL,4,NULL);



}