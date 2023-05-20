import sensor
import RPi.GPIO as GPIO
import time
import socket
import time
import fcntl

"""
本程序功能：
	通过 sensor.DHT11_ 类来采集环境温湿度数据
	将环境温湿度数据和采样时间写入本地文件data.txt
"""

if __name__ == "__main__":
    dht11_pin = 18  # 补全引脚名称
    GPIO.setmode(GPIO.BCM)
    DHT11 = sensor.DHT11_(dht11_pin)

    try:
        while True:
			
            flag, result = DHT11.read_data()
            time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            
            if flag == True:
				# 如果数据无误，则将其插入本地文件
                print("temperature: %-3.1f"% result[1])
                print("humidity: %-3.1f"% result[0])
                with open('data.txt', 'a') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # 上锁
                    f.write(str(result[1])+'　'+str(result[0])+'　'+str(time_now)+'\n')
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # 解锁
                print("Insert into file successfully.")
            else:
				# 如果数据出错，在本地文件内插入error条目
                print("ERROR: fail to collect data")
                with open('data.txt', 'a') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # 上锁
                    f.write('error'+'　'+'error'+'　'+str(time_now)+'\n')
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # 解锁
                print("Insert into file successfully.")
            
            print('\n')
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n Ctrl + C QUIT")
        
    finally:
        GPIO.cleanup()
