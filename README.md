# Two-link ROS 2 control

2관절 로봇의 키보드 명령과 시리얼 통신에 사용하는 ROS 2 패키지입니다.
이 저장소를 한 번 clone하면 아래 두 패키지가 함께 내려받아집니다.

| 패키지 | 역할 |
| --- | --- |
| `twolink_control` | 키보드 목표각 입력, ROS 토픽과 로봇 시리얼 통신 연결 |
| `twolink_msgs` | 목표 명령 `CMD`, 상태 피드백 `XYpos` 메시지 정의 |

## 실행 환경

- Ubuntu 22.04 / ROS 2 Humble 기준
- `colcon`, `rosdep`, Python 3
- 해당 시리얼 프로토콜을 구현한 로봇 제어 보드와 펌웨어

Arduino 펌웨어, 모터 드라이버 라이브러리, Gazebo 모델은 이 저장소에 포함되어 있지 않습니다.
실제 로봇을 움직이려면 호환되는 펌웨어가 이미 업로드되어 있어야 합니다.
Gazebo 없이 사용할 수 있습니다.

## 설치 및 빌드

ROS 2 Humble과 개발 도구가 설치된 환경에서 실행합니다.
`rosdep`은 최초 한 번 초기화되어 있어야 합니다(`sudo rosdep init`, `rosdep update`).

```bash
source /opt/ros/humble/setup.bash
cd ~/ros2_ws/src
git clone https://github.com/Stick-0/twolink_ros2.git .
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src --rosdistro humble -r -y
colcon build
source install/setup.bash
```

## 키보드 제어

터미널 1에서 시리얼 노드를 실행합니다. `port`는 실제 연결된 장치 경로로 설정합니다.

```bash
cd ros2_ws
source install/setup.bash
ros2 run twolink_control serial_node
```

터미널 2에서 키보드 노드를 실행하고 해당 터미널에 포커스를 둡니다.

```bash
cd ros2_ws
source install/setup.bash
ros2 run twolink_control command_node
```

| 키(영문 소문자) | 목표각 설정 |
| --- | --- |
| `e` / `d` | 1번 관절 목표각에 + / − `delta` 누적 |
| `r` / `f` | 2번 관절 목표각에 + / − `delta` 누적 |

각도 단위는 rad입니다. 기본 `delta=0.02`는 약 1.15도입니다.
첫 이동 키 입력 때 현재 측정각으로 목표를 초기화하고, 이후 입력은 목표각에 누적합니다.
화면의 `Desired`는 2π 주기로 보정해 `Current`에 가장 가까운 동치 각도로 표시합니다.
표시 보정은 누적된 목표각이나 실제 전송값을 변경하지 않습니다.

키보드 노드는 첫 `robot_state`를 받을 때까지 `Waiting for robot_state...`를 표시합니다.
피드백을 받은 뒤 첫 이동 키를 누르면 목표각 전송을 시작하며, 이후에는 마지막 목표를 반복 전송합니다.
대응하는 보드 펌웨어는 실행 상태에서 위치 피드백을 응답하므로 보드의 시작/정지 절차도 필요합니다.
`Ctrl+C`는 ROS 노드만 종료하며 보드의 정지 명령이 아닙니다. 보드가 마지막 목표를 유지할 수 있습니다.

## 자체 IK 또는 제어 프로그램 연결

키보드 노드 대신 사용자 노드가 `des_value`에 `twolink_msgs/msg/CMD`를 발행하면 됩니다.
`q1des`, `q2des`를 **둘 다** rad 단위로 설정해야 합니다.
다른 명령 노드와 키보드 노드를 동시에 발행시키면 서로의 목표를 덮어쓸 수 있습니다.

| 토픽(기본 네임스페이스) | 타입 | 내용 |
| --- | --- | --- |
| `/des_value` | `twolink_msgs/msg/CMD` | `xdes`, `ydes`, `q1des`, `q2des` |
| `/robot_state` | `twolink_msgs/msg/XYpos` | `xpos`, `ypos`, `xvel`, `yvel`, `qpos1`, `qpos2`, `qvel1`, `qvel2` |

현재 `serial_node`는 항상 관절 제어 명령 `J`를 사용합니다.
목표 관절각은 `q1des`, `q2des`이며, `xdes`, `ydes`에 끝단 좌표를 넣는 것만으로는 IK가 실행되지 않습니다.
이 패키지는 IK, 궤적 생성, 관절 범위 제한을 제공하지 않습니다.

## 보드 통신 규약

- 기본 포트 `/dev/ttyACM0`, 기본 속도 9600 baud
- 명령/상태 요청 타이머 0.1초(10 Hz)
- 관절 명령: ASCII `J` + little-endian float32 8개
- 명령 데이터 순서: `xdes, ydes, 0, 0, q1des, q2des, 0, 0`
- 상태 요청: ASCII `R`
- 상태 응답: 헤더/CRC 없이 32바이트, little-endian float32 8개
- 상태 데이터 순서: `x, y, vx, vy, q1, q2, dq1, dq2`
- 기본적으로 ASCII `D` 진단 요청도 사용하며, 보드 모드·적용 목표·모터 상태를 로그로 출력

`D` 진단을 지원하지 않는 펌웨어에서는 다음처럼 진단 요청을 끌 수 있습니다.

```bash
ros2 run twolink_control serial_node --ros-args -p board_diagnostics:=false
```
