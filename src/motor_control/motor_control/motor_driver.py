import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Int64MultiArray
import serial
import threading
import time

class Motor_Driver(Node):
    def __init__(self):
        super().__init__('Motor_Driver')

        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baud', 115200)

        #Parameters
        port= self.get_parameter('port').value
        baud= self.get_parameter('baud').value

        #Serial
        self.ser= serial.Serial(port, baud, timeout= 0.01)
        time.sleep(2)

        #ROS
        self.create_subscription(Twist,'/cmd_vel',self.cmd_vel_callback,10)
        self.encoder_pub= self.create_publisher(Int64MultiArray,'/wheel_ticks',10)

        #Threaded Serial Read
        self.running= True
        self.rx_thread= threading.Thread(target=self.read_serial)
        self.rx_thread.daemon= True
        self.rx_thread.start()

        try:
            self.ser.write("Reset\n".encode())
            self.get_logger().info("Encoder reset on startup")
            time.sleep(0.1)
        except Exception as e:
            self.get_logger().warn(f"Startup reset failed: {e}")

        self.get_logger().info('STM32 Motor Driver Started')
    
    #CMD_VEL
    def cmd_vel_callback(self, msg: Twist):
        cmd= f"<VEL,{msg.linear.x:.3f},{msg.angular.z:.3f}>\n"
        try:
            self.ser.write(cmd.encode())
        except Exception as e:
            self.ser.write("Reset")
            self.get_logger().error(f"Serial Failed: {e}")

    #Serial RX
    def read_serial(self):
        buffer= ""
        while self.running:
            try:
                data= self.ser.read().decode(errors='ignore')
                if data:
                    if data == '\n':
                        self.handle_line(buffer.strip())
                        buffer= ""
                    else:
                        buffer += data
            except Exception:
                pass

    #Handle STM Data
    def handle_line(self, line: str):
        if not line.startswith("<ENC"):
            return
        
        try:
            _,l,r= line.strip("<>").split(',')
            msg= Int64MultiArray()
            msg.data= [int(l), int(r)]
            self.encoder_pub.publish(msg)

        except Exception:
            self.get_logger().warn(f"Bad encoder frame: {line}")

    #Cleanup
    def destroy_node(self):
        try:
            reset_cmd = "Reset\n"   # or whatever protocol you define
            self.ser.write(reset_cmd.encode())
            self.get_logger().info("Sent encoder reset command")

            time.sleep(0.1)  # small delay to ensure STM32 processes it

        except Exception as e:
            self.get_logger().warn(f"Failed to send reset: {e}")

        self.running= False
        self.rx_thread.join(timeout= 1.0)
        #self.ser.write("Reset")
        self.ser.close()
        super().destroy_node()

def main():
    rclpy.init()
    node= Motor_Driver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__== '__main__':
    main()