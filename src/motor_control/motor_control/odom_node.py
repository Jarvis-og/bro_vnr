import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from std_msgs.msg import Int64MultiArray
from tf2_ros import TransformBroadcaster
import math

class Odom_Node(Node):
    def __init__(self):
        super().__init__('Odom_Node')

        self.declare_parameter('wheel_radius', 0.037)
        self.declare_parameter('wheel_base', 0.227)
        self.declare_parameter('tpr_left', 17350)
        self.declare_parameter('tpr_right', 17350)

        self.R= self.get_parameter('wheel_radius').value
        self.B= self.get_parameter('wheel_base').value
        self.TPR_L= self.get_parameter('tpr_left').value
        self.TPR_R= self.get_parameter('tpr_right').value

        #State
        self.x= 0.0
        self.y= 0.0
        self.theta= 0.0
        self.prev_left= 0.0
        self.prev_right= 0.0
        self.prev_time= 0.0
        #self.vth= 0.0
        #self.vx= 0.0

        self.create_subscription(Int64MultiArray, '/wheel_ticks', self.ticks_cb, 10)
        self.odom_pub= self.create_publisher(Odometry, '/odom', 10)
        self.get_logger().info("Odom Publisher started!")
    
    def ticks_cb(self, msg: Int64MultiArray):
        if len(msg.data) > 2:
            return

        l_ticks,r_ticks= msg.data
        now= self.get_clock().now()

        if self.prev_left == 0.0:
            self.prev_left= l_ticks
            self.prev_right= r_ticks
            self.prev_time= now

        dt= (now - self.prev_time).nanoseconds*1e-9
        if dt <= 0.0:
            return
        
        dl= l_ticks - self.prev_left
        dr= r_ticks - self.prev_right

        self.prev_left= l_ticks
        self.prev_right= r_ticks
        self.prev_time= now

        #Wheel Distance
        dL= (dl / self.TPR_L) * (2.0 * math.pi * self.R) #Distance per rotation
        dR= (dr / self.TPR_R) * (2.0 * math.pi * self.R)

        ds= (dR + dL) / 2.0 #Differential Equation
        dtheta= (dR - dL) /self.B

        #MidPoint of Robot in 2d Plane
        self.x += ds * math.cos(self.theta + dtheta / 2.0)
        self.y += ds * math.sin(self.theta + dtheta / 2.0)
        self.theta += dtheta

        vx= ds/dt #Velocity m/s
        vth= dtheta/dt #Velocity rad/s

        self.publish(now, vx, vth)

    def publish(self, stamp, vx, vth):
        qz= math.sin(self.theta / 2.0) #Quaternion Z
        qw= math.cos(self.theta / 2.0) #Quaternion W

        #Odometry
        odom= Odometry()
        odom.header.stamp= stamp.to_msg()
        odom.header.frame_id= 'odom'
        odom.child_frame_id= 'base_link'

        odom.pose.pose.position.x= self.x
        odom.pose.pose.position.y= self.y
        odom.pose.pose.orientation.z= qz
        odom.pose.pose.orientation.w= qw

        odom.twist.twist.linear.x= vx
        odom.twist.twist.angular.z= vth

        odom.pose.covariance[0] = 0.05
        odom.pose.covariance[7] = 0.05
        odom.pose.covariance[35] = 0.1
        
        odom.twist.covariance[0] = 0.1
        odom.twist.covariance[35] = 0.2        

        self.odom_pub.publish(odom)


def main():
    rclpy.init()
    node= Odom_Node()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()