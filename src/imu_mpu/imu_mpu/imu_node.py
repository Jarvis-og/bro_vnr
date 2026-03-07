import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import smbus2
import math

MPU_ADDR= 0x68
PWR_MGMT_1= 0x6B
ACCEL_XOUT= 0x3B
GYRO_XOUT= 0x43

class MPUNode(Node):
    def __init__(self):
        super().__init__('MPU_Node')

        self.declare_parameter('frame_id', 'imu_link')
        self.frame_id= self.get_parameter('frame_id').value

        self.bus= smbus2.SMBus(1)

        #Wake MPU6050
        self.bus.write_byte_data(MPU_ADDR, PWR_MGMT_1, 0x00)
        self.pub= self.create_publisher(Imu, '/imu/data', 10)
        self.timer= self.create_timer(0.01, self.update)
        
        self.get_logger().info("MPU6050 node started!")
                               
    def read_word(self,reg):
        high= self.bus.read_byte_data(MPU_ADDR, reg)
        low= self.bus.read_byte_data(MPU_ADDR, reg+1)
        val= (high << 8) + low
        if val >=0x8000:
            val-= 65536
        return val
    
    def update(self):
        try:
            ax= self.read_word(ACCEL_XOUT)
            ay= self.read_word(ACCEL_XOUT + 2)
            az= self.read_word(ACCEL_XOUT + 4)

            gx= self.read_word(GYRO_XOUT)
            gy= self.read_word(GYRO_XOUT + 2)
            gz= self.read_word(GYRO_XOUT + 4)

            #Convert to SI
            accel_scale= 16384.0
            gyro_scale= 131.0

            ax= (ax / accel_scale) * 9.80665
            ay= (ay / accel_scale) * 9.80665
            az= (az / accel_scale) * 9.80665

            gx= math.radians(gx / gyro_scale)
            gy= math.radians(gy / gyro_scale)
            gz= math.radians(gz / gyro_scale)

            msg= Imu()
            msg.header.stamp= self.get_clock().now().to_msg()
            msg.header.frame_id= self.frame_id

            #Orientation (EKF)
            msg.orientation_covariance[0]= -1.0

            if (gz <= 0.05):
                gz= 0.0
            
            msg.angular_velocity.x= gx
            msg.angular_velocity.y= gy
            msg.angular_velocity.z= gz

            msg.linear_acceleration.x= ax
            msg.linear_acceleration.y= ay
            msg.linear_acceleration.z= az

            # msg.angular_velocity_covariance= [0.05, 0.0, 0.0,
            #                                   0.0, 0.05, 0.0,
            #                                   0.0, 0.0, 0.2]

            # msg.linear_acceleration_covariance= [0.2, 0.0, 0.0,
            #                                      0.0, 0.2, 0.0,
            #                                      0.0, 0.0, 0.2]


            self.pub.publish(msg)
        
        except Exception as e:
            self.get_logger().info(e)

def main():
    rclpy.init()
    node= MPUNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
