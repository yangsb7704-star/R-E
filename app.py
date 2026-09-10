import math
import textwrap
import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# =============================
# 기본 설정
# =============================
st.set_page_config(page_title="모빌리티 구동계 초기 설계 도움 시스템", layout="wide")

PRESETS = {
    1: dict(scale='student', purpose='전동 킥보드형 퍼스널 모빌리티', mass=15, speed=15, unit='kmh', wheels=2, env='indoor', extra='경량 프레임, 접이식 구조'),
    2: dict(scale='research', purpose='스위피형 실내 청소로봇', mass=75, speed=1.2, unit='mps', wheels=2, env='indoor', extra='물탱크, 브러시, 저소음 감속기'),
    3: dict(scale='research', purpose='카고형 고하중 물류로봇', mass=365, speed=1.2, unit='mps', wheels=4, env='obstacle', extra='고하중 우레탄 바퀴, 자동 제동'),
    4: dict(scale='industry', purpose='초소형 전기차형 모빌리티', mass=562, speed=80, unit='kmh', wheels=4, env='normal', extra='강성 프레임, 독립 서스펜션'),
    5: dict(scale='research', purpose='산악 구조 보조 로봇', mass=50, speed=0.5, unit='mps', wheels=4, env='extreme', extra='궤도 트랙, 방수방진, 카메라'),
    6: dict(scale='industry', purpose='농업용 방제 로봇', mass=150, speed=1.0, unit='mps', wheels=4, env='extreme', extra='방제 펌프, 부식 방지 프레임'),
    7: dict(scale='student', purpose='FRC/대회용 공 수집 및 발사 로봇', mass=55, speed=2.0, unit='mps', wheels=4, env='indoor', extra='intake, feeder, shooter, waterwheel, 알루미늄 프로파일'),
    8: dict(scale='research', purpose='지능형 서비스 안내 로봇', mass=45, speed=1.0, unit='mps', wheels=2, env='indoor', extra='2D LiDAR, 카메라, LED 디스플레이'),
    9: dict(scale='research', purpose='궤도형 험지 탐사 로봇', mass=80, speed=0.7, unit='mps', wheels=4, env='extreme', extra='무한궤도, 장애물 극복, 센서 마스트'),
}

SCALE_LABELS = {
    'student': '학생용/공모전·탐구용',
    'research': '연구용/프로토타입용',
    'industry': '산업용/고하중·전문 제작용'
}

ENV_LABELS = {
    'normal': '단순 이동/평지 중심',
    'indoor': '실내 자율 이동/완만한 경사',
    'obstacle': '장애물이 많은 지형/요철',
    'extreme': '험한 지형/급경사·비포장'
}

# =============================
# 유틸 함수
# =============================
def env_grade(env):
    return {'normal': 2, 'indoor': 8, 'obstacle': 15, 'extreme': 35}.get(env, 8)


def parse_float(value, default):
    if value is None or str(value).strip() == '':
        return default
    try:
        return float(str(value).strip())
    except ValueError:
        return default


def parse_int(value, default):
    if value is None or str(value).strip() == '':
        return default
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return default


def stars(n):
    return '★' * n + '☆' * (5 - n)


def safe_lower(text):
    return str(text).lower() if text is not None else ''


def contains_any(text, keywords):
    lower = safe_lower(text)
    return any(k.lower() in lower for k in keywords)

# =============================
# 부품 분류 및 예산 로직
# =============================
def classify_parts(req_power, scale):
    if req_power <= 60 and scale != 'industry':
        return dict(
            tier='소형', wheel_r=0.05, motor_rpm=4000, motor_nm=0.10,
            motor='Parvalux PBL42 Range BLDC 모터 / 24~48V / 4000rpm / 26~42W / 연속토크 0.06~0.10Nm', motor_cost=85000,
            gear='미스미 소모듈 평기어 M0.8~1.0 / 압력각 20도 / C3604 황동 또는 POM', gear_cost=18000,
            wheel='100mm 우레탄·고무 로봇 바퀴 + Ø6mm SUS304 축 + 소형 베어링', wheel_cost=18000,
            control='Arduino·ESP32 제어보드 + 소형 DC·BLDC 드라이버 + 12~24V 배터리', control_cost=120000,
            frame='PLA·PETG 3D 프린팅 브라켓 + 소형 알루미늄 프로파일', frame_cost=90000
        )
    if req_power <= 220 and scale != 'industry':
        return dict(
            tier='중소형', wheel_r=0.10, motor_rpm=3000, motor_nm=0.50,
            motor='Parvalux PBL60 Range BLDC 모터 / 24~48V / 3000rpm / 104~157W / 연속토크 0.33~0.50Nm', motor_cost=240000,
            gear='PGx42·GB28급 기어헤드 또는 미스미 평기어 M2.0 S45C', gear_cost=65000,
            wheel='200mm 솔리드 우레탄 바퀴 + Ø10mm S45C 축 + 플랜지 베어링', wheel_cost=55000,
            control='24V BLDC 드라이버 2~4ch + 24V 10~20Ah 리튬 배터리 + 퓨즈', control_cost=420000,
            frame='2020·3030 알루미늄 프로파일 프레임 + 3D프린팅 모터마운트', frame_cost=180000
        )
    if req_power <= 650 or scale == 'research':
        return dict(
            tier='중형', wheel_r=0.12, motor_rpm=4000, motor_nm=1.40,
            motor='Parvalux PBL86 Range BLDC 모터 / 48V / 4000rpm / 419~586W / 연속토크 1.00~1.40Nm', motor_cost=480000,
            gear='Parvalux PGx70·PGx52 기어박스 또는 미스미 경제형 평기어 M3.0 / GB/T 10095 8등급', gear_cost=101396,
            wheel='250mm 고하중 우레탄 바퀴 + Ø15mm S45C 열처리 축 + 하우징 베어링', wheel_cost=95000,
            control='48V BLDC 드라이버 + 48V 20Ah 배터리팩 + BMS + 비상정지 스위치', control_cost=900000,
            frame='3030·4040 알루미늄 프로파일 또는 절곡 알루미늄 판재 섀시', frame_cost=350000
        )
    return dict(
        tier='대형', wheel_r=0.25, motor_rpm=3000, motor_nm=8.00,
        motor='AC 서보모터 SD13·SD48급 또는 산업용 BLDC 서보 / 1kW 이상급 / 인버터 제어', motor_cost=1200000,
        gear='헬리컬·웜 감속기 또는 LIW·MWS급 고토크 기어헤드 / 28~45Nm급 이상', gear_cost=850000,
        wheel='13인치 이상 튜브·솔리드 타이어 + Ø20mm 이상 구동축 + 자동차형 베어링', wheel_cost=220000,
        control='서보 드라이브·인버터 + 48V~고전압 배터리팩 + BMS + 차단기', control_cost=3500000,
        frame='강철 사각파이프 용접 프레임 또는 주문제작 절곡 섀시', frame_cost=2200000
    )


def aux_items(extra):
    e = safe_lower(extra)
    items = []
    if contains_any(e, ['intake', '인테이크']):
        items.append(('보조 기구부', 'Intake 흡입 롤러용 775·550급 DC 모터 또는 소형 BLDC + 고무 롤러 + 벨트', 95000, 1, '바닥의 공·물체를 로봇 내부로 끌어올림'))
    if contains_any(e, ['feeder', '피더']):
        items.append(('보조 기구부', 'Feeder 이송용 서보모터·기어드 DC 모터 + 타이밍벨트 풀리', 80000, 1, '수집된 물체를 슈터나 저장부로 일정하게 공급'))
    if contains_any(e, ['shooter', '슈터']):
        items.append(('보조 기구부', 'Shooter 고속 플라이휠용 BLDC·DC 모터 2개 + 플라이휠 + 모터 브라켓', 140000, 2, '고속 회전 휠로 공을 목표 방향으로 발사'))
    if contains_any(e, ['waterwheel', '워터휠']):
        items.append(('보조 기구부', 'Waterwheel·색인 휠용 AC·BLDC 보조모터 + 원판형 휠', 120000, 1, '공 또는 물체의 방향과 공급 순서를 제어'))
    if contains_any(e, ['lift', '리프트', '엘리베이터']):
        items.append(('보조 기구부', 'Lift 승강용 웜기어드 모터 + 리니어 가이드 + 랙기어', 160000, 1, '상하 이동 또는 높이 조절 기능 수행'))
    if contains_any(e, ['lidar', '라이다', '카메라', '센서']):
        items.append(('센서·인식부', '2D LiDAR·카메라·초음파 센서 묶음 + 마운트', 220000, 1, '자율 이동과 장애물 인식'))
    if contains_any(e, ['트랙', '궤도', 'track']):
        items.append(('주행 보강부', '소형 무한궤도 트랙 키트 또는 고무 트랙 벨트 세트', 180000, 2, '접지 면적을 늘려 험지 주행 안정성 향상'))
    if contains_any(e, ['방수', '방진']):
        items.append(('보호 구조', '방수 커넥터 + 실링 고무 + 전장 박스 방수 케이스', 90000, 1, '야외·먼지 환경에서 전장부 보호'))
    return items

# =============================
# 해석 로직
# =============================
def analyze(data):
    scale = data['scale']
    mass = data['mass']
    speed = data['speed']
    unit = data['unit']
    wheels = max(1, data['wheels'])
    env = data['env']
    speed_mps = speed / 3.6 if unit == 'kmh' else speed
    grade = env_grade(env)

    g, crr, sf, eff = 9.81, 0.02, 1.5, 0.85
    base_res = crr * mass * g * math.cos(math.radians(grade)) + mass * g * math.sin(math.radians(grade))
    req_force = base_res * sf
    req_power = base_res * speed_mps * sf

    part = classify_parts(req_power, scale)
    req_tq = req_force * part['wheel_r'] / wheels
    req_rpm = speed_mps / (2 * math.pi * part['wheel_r']) * 60 if part['wheel_r'] > 0 else 0
    ideal = part['motor_rpm'] / max(req_rpm, 1)

    # 요구 토크를 만족하도록 최소 모터 토크 보정
    motor_nm = max(part['motor_nm'], req_tq / (max(ideal, 1) * eff) * 1.45)
    center = max(2, round(ideal))

    ratios = []
    for d in range(-2, 4):
        r = max(1, center + d)
        if r not in ratios:
            ratios.append(r)
    for r in [3, 4, 5, 6, 8, 10, 12]:
        if len(ratios) >= 6:
            break
        if r not in ratios:
            ratios.append(r)

    rows = []
    for r in ratios:
        rpm = part['motor_rpm'] / r
        tq = motor_nm * r * eff
        margin = (tq - req_tq) / max(req_tq, 0.001) * 100
        speed_err = abs(rpm - req_rpm) / max(req_rpm, 1) * 100
        score = 100 - speed_err * 0.65 + min(max(margin, 0), 120) * 0.18

        if r < center:
            typ = '속도형'
            reason = '감속비가 낮아 휠 RPM이 높음. 빠른 주행에는 유리하지만 등판·하중 여유는 상대적으로 작음.'
        elif r > center:
            typ = '토크형'
            reason = '감속비가 높아 휠 토크가 커짐. 험지·고하중에는 유리하지만 최고속도는 낮아짐.'
        else:
            typ = '균형형'
            reason = '목표 속도와 요구 토크의 균형이 가장 좋아 초기 설계 기준안으로 적합.'

        rows.append(dict(
            ratio=r,
            rpm=rpm,
            tq=tq,
            margin=margin,
            speed_err=speed_err,
            score=score,
            typ=typ,
            reason=reason,
            driven=20 * r
        ))

    rows = sorted(rows, key=lambda x: x['score'], reverse=True)[:5]
    for i, row in enumerate(rows):
        row['stars'] = 5 - i

    return part, rows, dict(
        speed_mps=speed_mps,
        speed_kmh=speed_mps * 3.6,
        grade=grade,
        req_power=req_power,
        req_tq=req_tq,
        req_rpm=req_rpm,
        motor_nm=motor_nm,
        req_force=req_force
    )

# =============================
# 스케치 판별 및 도면 함수
# =============================
def get_mobility_type(data):
    text = f"{data.get('purpose', '')} {data.get('extra', '')}".lower()
    if any(k in text for k in ['킥보드', 'scooter']):
        return 'scooter'
    if any(k in text for k in ['전기차', '자동차', 'ev', '트위지', 'car']):
        return 'car'
    if any(k in text for k in ['궤도', '트랙', 'track', '험지 탐사']):
        return 'tracked'
    if any(k in text for k in ['청소', '스위피', '브러시']):
        return 'cleaner'
    if any(k in text for k in ['서비스', '안내', '디스플레이']):
        return 'service'
    if any(k in text for k in ['frc', '대회', '슈터', 'shooter', 'intake']):
        return 'competition'
    if any(k in text for k in ['농업', '방제', '펌프']):
        return 'agri'
    return 'generic'


def rounded_box(ax, xy, w, h, edge, lw=3.2, radius=24, fill=False, face='none', z=2):
    box = patches.FancyBboxPatch(
        xy, w, h,
        boxstyle=f"round,pad=0.02,rounding_size={radius}",
        linewidth=lw, edgecolor=edge, facecolor=face if fill else 'none', zorder=z
    )
    ax.add_patch(box)
    return box


def label(ax, text, xy, xytext, color='#174a8b', size=10):
    # 라벨과 화살표가 본체 위를 지나가지 않게 외곽으로 배치
    ax.annotate(
        text, xy=xy, xytext=xytext,
        arrowprops=dict(arrowstyle='->', color=color, lw=2.0, shrinkA=3, shrinkB=3),
        color=color, fontsize=size, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.22', facecolor='white', edgecolor=color, alpha=0.96),
        zorder=5
    )


def draw_wheel(ax, x, y, r, color='#cc3333'):
    ax.add_patch(patches.Circle((x, y), r, fill=False, edgecolor=color, lw=3.4, zorder=3))
    ax.add_patch(patches.Circle((x, y), r * 0.42, fill=False, edgecolor=color, lw=2.6, zorder=3))
    ax.add_patch(patches.Circle((x, y), r * 0.12, fill=True, facecolor=color, edgecolor=color, zorder=3))


def draw_sketch(data, part, best):
    """초기 배치 스케치 자료를 참고한 둥근 선형 배치도.
    - 본체/외형: 붉은색 계열
    - 장치/라벨/화살표: 파란색 계열
    - 글씨는 외곽에 배치해 도형과 겹치지 않게 구성
    """
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.set_xlim(0, 1200)
    ax.set_ylim(760, 0)
    ax.axis('off')
    ax.set_facecolor('white')

    red = '#c9362e'
    blue = '#1d56d6'
    purple = '#7b4ee6'
    green = '#157a44'
    gray = '#5c6770'

    mtype = get_mobility_type(data)
    extra = data.get('extra', '')
    e = safe_lower(extra)

    # 제목 영역
    ax.text(60, 62, '초기 배치 스케치', fontsize=18, fontweight='bold', color='#1f2937')
    wrapped_purpose = textwrap.fill(data.get('purpose', '모빌리티'), width=42)
    ax.text(60, 95, wrapped_purpose, fontsize=11.5, color='#374151')

    # 공통 장치 위치 변수
    motor_xy = (235, 438)
    gearbox_xy = (325, 438)
    battery_xy = (565, 402)

    # -------------------------
    # 외형별 본체 스케치
    # -------------------------
    if mtype == 'scooter':
        # 킥보드형: 낮은 데크 + 핸들바 + 앞/뒤 바퀴
        ax.plot([210, 800], [505, 505], color=red, lw=5, solid_capstyle='round')
        rounded_box(ax, (260, 462), 390, 42, red, lw=3.5, radius=20)
        ax.plot([755, 710], [210, 505], color=red, lw=4, solid_capstyle='round')
        ax.plot([690, 805], [210, 210], color=red, lw=4, solid_capstyle='round')
        draw_wheel(ax, 260, 548, 55, red)
        draw_wheel(ax, 760, 548, 55, red)
        motor_xy = (285, 485)
        gearbox_xy = (340, 485)
        battery_xy = (490, 475)
        label(ax, 'Drive Motor', motor_xy, (80, 615), blue)
        label(ax, 'Handle / Control', (748, 225), (820, 165), blue)

    elif mtype == 'car':
        # 자동차형: 온전한 차체 실루엣 + 4륜 느낌
        rounded_box(ax, (180, 330), 760, 190, red, lw=4.2, radius=40)
        ax.plot([290, 420, 730, 840], [330, 220, 220, 330], color=red, lw=4.2, solid_capstyle='round')
        ax.plot([455, 455], [230, 330], color=red, lw=2.4)
        ax.plot([710, 710], [230, 330], color=red, lw=2.4)
        draw_wheel(ax, 315, 545, 62, red)
        draw_wheel(ax, 805, 545, 62, red)
        motor_xy = (250, 438)
        gearbox_xy = (345, 438)
        battery_xy = (585, 402)
        label(ax, 'Drive Motor', motor_xy, (70, 625), blue)
        label(ax, 'Suspension / Frame', (800, 370), (885, 260), blue)

    elif mtype == 'tracked':
        # 궤도형: 둥근 트랙 벨트 + 내부 보기륜
        rounded_box(ax, (160, 425), 790, 155, red, lw=4.4, radius=78)
        rounded_box(ax, (230, 265), 640, 185, red, lw=4.0, radius=44)
        for x, r in [(280, 48), (485, 38), (690, 38), (825, 48)]:
            draw_wheel(ax, x, 503, r, red)
        motor_xy = (265, 390)
        gearbox_xy = (355, 390)
        battery_xy = (560, 340)
        label(ax, 'Track Drive Motor', motor_xy, (55, 640), blue)
        label(ax, 'Rubber Track', (840, 505), (900, 620), blue)

    elif mtype == 'cleaner':
        # 청소로봇형: 낮고 둥근 캡슐형 본체 + 브러시/탱크
        rounded_box(ax, (190, 300), 760, 235, red, lw=4.0, radius=85)
        draw_wheel(ax, 310, 555, 48, red)
        draw_wheel(ax, 800, 555, 48, red)
        ax.add_patch(patches.Circle((555, 520), 42, fill=False, edgecolor=green, lw=3.2))
        rounded_box(ax, (505, 335), 160, 70, green, lw=3.0, radius=22)
        motor_xy = (255, 450)
        gearbox_xy = (345, 450)
        battery_xy = (575, 370)
        label(ax, 'Brush Motor', (555, 520), (885, 640), green)
        label(ax, 'Water Tank', (585, 360), (830, 235), green)

    elif mtype == 'service':
        # 서비스 안내형: 세로형 바디 + 디스플레이 + 2륜 베이스
        rounded_box(ax, (380, 215), 320, 320, red, lw=4.0, radius=70)
        rounded_box(ax, (430, 250), 220, 105, blue, lw=3.0, radius=22)
        draw_wheel(ax, 410, 560, 50, red)
        draw_wheel(ax, 670, 560, 50, red)
        motor_xy = (415, 475)
        gearbox_xy = (500, 475)
        battery_xy = (560, 430)
        label(ax, 'Display / UI', (535, 300), (790, 210), blue)
        label(ax, '2D LiDAR / Camera', (540, 215), (80, 205), blue)

    elif mtype == 'competition':
        # 대회용: 첨부 스케치처럼 둥근 직사각형 섀시 + 상부 슈터 + 전면 인테이크
        rounded_box(ax, (190, 315), 760, 210, red, lw=4.2, radius=42)
        ax.plot([275, 405, 735, 860], [315, 205, 205, 315], color=red, lw=4.2, solid_capstyle='round')
        draw_wheel(ax, 320, 550, 58, red)
        draw_wheel(ax, 805, 550, 58, red)
        motor_xy = (250, 425)
        gearbox_xy = (350, 425)
        battery_xy = (565, 390)
        # 기본 대회 장치 배치
        rounded_box(ax, (820, 370), 145, 80, purple, lw=3.6, radius=18)
        rounded_box(ax, (560, 150), 165, 92, purple, lw=3.6, radius=18)
        rounded_box(ax, (405, 265), 135, 65, purple, lw=3.2, radius=18)
        ax.add_patch(patches.Circle((655, 330), 36, fill=False, edgecolor=purple, lw=3.2))
        label(ax, 'Intake', (890, 410), (955, 610), purple)
        label(ax, 'Shooter Motors', (642, 180), (780, 120), purple)
        label(ax, 'Feeder', (455, 300), (70, 270), purple)
        label(ax, 'Index Wheel', (655, 330), (820, 330), purple)

    elif mtype == 'agri':
        # 농업용: 높은 지상고 + 탱크/펌프 + 큰 바퀴
        rounded_box(ax, (180, 285), 760, 200, red, lw=4.2, radius=40)
        rounded_box(ax, (460, 190), 210, 105, green, lw=3.4, radius=38)
        ax.plot([220, 890], [485, 485], color=red, lw=4.0)
        draw_wheel(ax, 290, 555, 70, red)
        draw_wheel(ax, 820, 555, 70, red)
        motor_xy = (245, 430)
        gearbox_xy = (350, 430)
        battery_xy = (600, 395)
        label(ax, 'Pump / Tank', (565, 225), (790, 185), green)
        label(ax, 'Large Tire', (820, 555), (910, 655), blue)

    else:
        # 일반 로봇형
        rounded_box(ax, (190, 315), 760, 210, red, lw=4.2, radius=42)
        draw_wheel(ax, 320, 550, 58, red)
        draw_wheel(ax, 805, 550, 58, red)
        if data.get('wheels', 4) >= 6:
            draw_wheel(ax, 565, 560, 46, red)
        motor_xy = (250, 425)
        gearbox_xy = (350, 425)
        battery_xy = (565, 390)

    # -------------------------
    # 공통 주요 장치 배치
    # -------------------------
    rounded_box(ax, (motor_xy[0] - 55, motor_xy[1] - 28), 92, 56, blue, lw=3.2, radius=12)
    ax.add_patch(patches.Circle((gearbox_xy[0], gearbox_xy[1]), 28, fill=False, edgecolor=blue, lw=3.2, zorder=4))
    rounded_box(ax, (battery_xy[0] - 75, battery_xy[1] - 32), 150, 64, blue, lw=3.2, radius=12)

    # 본체와 겹치지 않도록 라벨은 바깥쪽에 배치
    label(ax, 'Drive Motor', motor_xy, (60, 705), blue)
    label(ax, f'{best["ratio"]}:1 Gearbox', gearbox_xy, (315, 685), blue)
    label(ax, 'Battery / Controller', battery_xy, (690, 705), blue)

    # 기타 요구사항 기반 추가 장치: 없는 경우에는 중복 생성하지 않음
    if mtype != 'competition':
        if contains_any(e, ['intake', '인테이크']):
            rounded_box(ax, (855, 395), 120, 70, purple, lw=3.2, radius=18)
            label(ax, 'Intake', (915, 430), (940, 610), purple)
        if contains_any(e, ['feeder', '피더']):
            rounded_box(ax, (405, 250), 135, 65, purple, lw=3.2, radius=18)
            label(ax, 'Feeder', (470, 280), (70, 265), purple)
        if contains_any(e, ['shooter', '슈터']):
            rounded_box(ax, (565, 145), 165, 92, purple, lw=3.2, radius=18)
            label(ax, 'Shooter Motors', (650, 175), (790, 115), purple)
        if contains_any(e, ['waterwheel', '워터휠']):
            ax.add_patch(patches.Circle((665, 330), 36, fill=False, edgecolor=purple, lw=3.2, zorder=4))
            label(ax, 'Index Wheel', (665, 330), (830, 330), purple)

    if contains_any(e, ['카메라', '라이다', 'lidar', '센서']) or mtype in ['service', 'tracked']:
        ax.add_patch(patches.Circle((610, 245), 18, fill=False, edgecolor=gray, lw=2.8, zorder=4))
        label(ax, 'Sensor', (610, 245), (60, 150), gray)

    # 하단 메모 박스: 그림과 분리하여 중첩 방지
    memo = (
        f"Scale: {SCALE_LABELS.get(data['scale'], data['scale'])}   |   "
        f"Env: {ENV_LABELS.get(data['env'], data['env'])}   |   "
        f"Wheel radius: {part['wheel_r']*100:.0f}cm   |   "
        f"Gear: {best['ratio']}:1"
    )
    ax.text(60, 735, memo, fontsize=10.5, color='#4b5563')
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)

# =============================
# Fusion 360 기어 도면
# =============================
def draw_fusion_gear(best_ratio, mass):
    module_val = 1.0 if mass <= 30 else 2.0
    drive_teeth = 20
    driven_teeth = int(20 * best_ratio)
    r_drive = drive_teeth * module_val / 2
    r_driven = driven_teeth * module_val / 2
    center_dist = r_drive + r_driven

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_facecolor('white')
    ax.set_title('Fusion 360 기어 도면', fontsize=14, fontweight='bold')

    ax.add_patch(patches.Circle((0, 0), r_drive, fill=False, edgecolor='#2563eb', lw=2.6, linestyle='--'))
    ax.add_patch(patches.Circle((center_dist, 0), r_driven, fill=False, edgecolor='#dc2626', lw=2.6, linestyle='--'))
    ax.plot([0, center_dist], [0, 0], color='#111827', lw=1.8, linestyle='-.')
    ax.plot(0, 0, 'ko')
    ax.plot(center_dist, 0, 'ko')
    ax.text(0, r_drive + 5, f'구동기어 {drive_teeth}T', ha='center', color='#2563eb', fontsize=10)
    ax.text(center_dist, r_driven + 5, f'피동기어 {driven_teeth}T', ha='center', color='#dc2626', fontsize=10)
    ax.text(center_dist/2, -max(r_drive, r_driven)*0.28 - 8, f'중심거리 {center_dist:.1f} mm', ha='center', fontsize=10, color='#111827')
    ax.set_xlim(-r_drive - 25, center_dist + r_driven + 25)
    ax.set_ylim(-max(r_drive, r_driven)-25, max(r_drive, r_driven)+25)
    plt.tight_layout()
    return fig, center_dist, module_val, driven_teeth

# =============================
# 프로세스 설명 및 복사 내용
# =============================
def process_description(data, part, best):
    extra = data.get('extra', '')
    e = safe_lower(extra)
    lines = []
    lines.append('이 초기 배치 스케치는 완성 외형 렌더링이 아니라, 제작 전 장치 위치와 동력 흐름을 잡기 위한 개념도입니다.')
    lines.append(f"주행 구동부는 {part['motor']}를 기준으로 하며, 모터 회전은 {best['ratio']}:1 감속기를 거쳐 바퀴축으로 전달됩니다.")
    lines.append('배터리와 제어기는 차체 중앙부에 배치해 무게중심을 낮추고, 좌우 구동부에 전원을 분배하는 구조로 가정했습니다.')
    if contains_any(e, ['intake', '인테이크']):
        lines.append('인테이크는 전면 하단에 배치하여 이동 중 물체를 먼저 받아들이고, 롤러 회전으로 내부 이송부에 넘기는 역할을 합니다.')
    if contains_any(e, ['feeder', '피더']):
        lines.append('피더는 인테이크 뒤쪽 또는 중앙 경로에 배치되어 수집된 물체를 슈터·저장부로 일정하게 공급합니다.')
    if contains_any(e, ['shooter', '슈터']):
        lines.append('슈터는 상부 또는 후방 상단에 배치하여 고속 플라이휠 모터로 물체를 발사하는 기능을 담당합니다.')
    if contains_any(e, ['waterwheel', '워터휠']):
        lines.append('워터휠 또는 색인 휠은 피더와 슈터 사이에서 물체의 방향과 공급 순서를 정렬하는 역할을 합니다.')
    if contains_any(e, ['트랙', '궤도', 'track']):
        lines.append('궤도 트랙은 바퀴보다 접지 면적을 넓혀 미끄러짐을 줄이고 험지에서 안정적인 추진력을 확보하는 역할을 합니다.')
    if contains_any(e, ['카메라', '라이다', 'lidar', '센서']):
        lines.append('센서부는 전방 또는 상단에 배치해 장애물 인식, 위치 추정, 자율 주행 판단에 활용됩니다.')
    lines.append('실제 제작에서는 이 배치를 기준으로 Fusion 360에서 프레임, 모터마운트, 축 지지대, 배터리 브라켓을 순서대로 모델링하면 됩니다.')
    return '\n'.join([f'- {line}' for line in lines])


def build_report_text(data, part, rows, calc, budget, total):
    best = rows[0]
    budget_lines = '\n'.join([f"- {cat}: {name} / 단가 {unit:,}원 × {qty}개 = {unit*qty:,}원" for cat, name, unit, qty, *role in budget])
    gear_lines = '\n'.join([f"- {i}위 {stars(r['stars'])}: {r['ratio']}:1, 20T:{r['driven']}T, {r['typ']}, {r['reason']}" for i, r in enumerate(rows, 1)])
    return f"""[모빌리티 구동계 초기 설계 요약]

1. 입력 조건
- 제작 스케일: {SCALE_LABELS.get(data['scale'], data['scale'])}
- 용도: {data['purpose']}
- 질량: {data['mass']} kg
- 목표 속도: {data['speed']} {data['unit']}
- 구동 바퀴 수: {data['wheels']}개
- 운행 환경: {ENV_LABELS.get(data['env'], data['env'])}
- 기타 요구사항: {data['extra']}

2. 물리 모델 결과
- 요구 동력: {calc['req_power']:.0f} W
- 바퀴당 요구 토크: {calc['req_tq']:.2f} Nm
- 필요 휠 RPM: {calc['req_rpm']:.1f} RPM
- 추천 모터: {part['motor']}

3. 기어비 후보
{gear_lines}

4. 예산안
{budget_lines}
- 총 예상 제작 비용: 약 {total:,}원

5. 초기 설계 프로세스
{process_description(data, part, best)}
"""

# =============================
# Streamlit UI
# =============================
st.title('⚙️ 모빌리티 구동계 초기 설계 도움 시스템')
st.caption('제작자가 로봇 설계를 시작할 수 있도록 구동계 계산, 기어비 후보, 예산안, 초기 배치 스케치를 제공하는 보조 도구입니다.')

with st.sidebar:
    st.header('입력 방식 선택')
    option_list = ['직접 입력'] + [f"{k}. {v['purpose']} ({v['mass']}kg)" for k, v in PRESETS.items()]
    selected_option = st.selectbox('프리셋 선택', option_list)

    st.divider()
    st.subheader('직접 상세 조건 입력')
    st.caption('직접 입력을 선택하면 아래 입력값이 사용됩니다. 비워두면 내부 기본값으로 계산됩니다.')

    if selected_option == '직접 입력':
        scale_label = st.selectbox(
            '1. 로봇 제작 스케일/용도',
            ['선택 안 함', '학생용/공모전·탐구용', '연구용/프로토타입용', '산업용/고하중·전문 제작용'],
            index=0
        )
        scale_map = {
            '학생용/공모전·탐구용': 'student',
            '연구용/프로토타입용': 'research',
            '산업용/고하중·전문 제작용': 'industry'
        }
        scale = scale_map.get(scale_label, 'student')

        purpose_input = st.text_input('2. 목표 모빌리티의 용도', value='', placeholder='예: FRC/대회용 공 수집 및 발사 로봇')
        mass_input = st.text_input('3. 예상 총 질량 (kg)', value='', placeholder='예: 55')
        speed_input = st.text_input('4. 목표 주행 속도', value='', placeholder='예: 2.0')
        unit_label = st.selectbox('5. 속도 단위', ['m/s', 'km/h'], index=0)
        wheels_input = st.text_input('6. 구동 바퀴 수', value='', placeholder='예: 4')
        env_label = st.selectbox(
            '7. 로봇 운행 환경',
            ['선택 안 함', '단순 이동/평지 중심', '실내 자율 이동/완만한 경사', '장애물이 많은 지형/요철', '험한 지형/급경사·비포장'],
            index=0
        )
        env_map = {
            '단순 이동/평지 중심': 'normal',
            '실내 자율 이동/완만한 경사': 'indoor',
            '장애물이 많은 지형/요철': 'obstacle',
            '험한 지형/급경사·비포장': 'extreme'
        }
        env = env_map.get(env_label, 'indoor')
        extra_input = st.text_area(
            '8. 기타 요구사항',
            value='',
            placeholder='예: intake, feeder, shooter, waterwheel, 알루미늄 프로파일, 방수방진 등\n상세할수록 모빌리티가 더 구체화됩니다.',
            height=110
        )

        data = dict(
            scale=scale,
            purpose=purpose_input.strip() or '학생용 이동 로봇',
            mass=parse_float(mass_input, 35.0),
            speed=parse_float(speed_input, 1.5),
            unit='kmh' if unit_label == 'km/h' else 'mps',
            wheels=parse_int(wheels_input, 4),
            env=env,
            extra=extra_input.strip() or '없음'
        )
    else:
        preset_key = int(selected_option.split('.')[0])
        data = PRESETS[preset_key].copy()
        st.info('현재 빠른 스펙 프리셋이 적용되었습니다. 직접 입력을 원하면 위에서 직접 입력을 선택하세요.')

# 분석 실행
part, rows, calc = analyze(data)
best = rows[0]

# 입력 요약
st.subheader('0. 입력 조건 요약')
summary_cols = st.columns(4)
summary_cols[0].metric('제작 스케일', SCALE_LABELS.get(data['scale'], data['scale']))
summary_cols[1].metric('질량', f"{data['mass']:.1f} kg")
summary_cols[2].metric('목표 속도', f"{calc['speed_kmh']:.1f} km/h")
summary_cols[3].metric('운행 환경', ENV_LABELS.get(data['env'], data['env']))
st.write(f"**용도:** {data['purpose']}")
st.write(f"**기타 요구사항:** {data['extra']}")

# 물리 모델 결과
st.subheader('1. 물리 모델 분석 결과')
col1, col2, col3, col4 = st.columns(4)
col1.metric('요구 동력', f"{calc['req_power']:.0f} W")
col2.metric('바퀴당 요구 토크', f"{calc['req_tq']:.2f} Nm")
col3.metric('필요 휠 RPM', f"{calc['req_rpm']:.1f} RPM")
col4.metric('적용 경사각', f"{calc['grade']}°")

st.markdown('**추천 모터 사양**')
st.info(part['motor'] + f"\n\n기준 보정 토크: {calc['motor_nm']:.2f} Nm")

# 기어비 분석
st.subheader('2. 기어비 후보 분석')
st.table([
    {
        '순위/추천도': f"{i}위 {stars(r['stars'])}",
        '기어비': f"{r['ratio']}:1",
        '기어 잇수': f"20T : {r['driven']}T",
        '예상 휠 RPM': f"{r['rpm']:.1f}",
        '예상 휠 토크': f"{r['tq']:.2f} Nm",
        '유형': r['typ'],
        '추천도 선정 이유': r['reason']
    } for i, r in enumerate(rows, 1)
])

st.caption('별점은 목표 휠 RPM과의 차이, 요구 토크 대비 여유, 속도·토크 균형을 함께 고려해 산정합니다. 험지·고하중이면 별점이 조금 낮더라도 토크형 후보를 선택할 수 있습니다.')

# 예산안
st.subheader('3. 정밀 예산안')
budget = [
    ('주행 구동부', part['motor'], part['motor_cost'], data['wheels'], '주행을 위한 핵심 모터'),
    ('주행 구동부', part['gear'], part['gear_cost'], data['wheels'], '모터 회전을 감속해 토크를 증폭'),
    ('바퀴/축/베어링', part['wheel'], part['wheel_cost'], data['wheels'], '바닥 접지와 하중 지지'),
    ('제어/전원부', part['control'], part['control_cost'], 1, '전원 공급과 모터 제어'),
    ('주요 구성 형체', part['frame'], part['frame_cost'], 1, '차체 뼈대와 모터마운트 구성')
] + aux_items(data['extra'])

total = sum(x[2] * x[3] for x in budget)
st.table([
    {
        '분류': cat,
        '상세 품명 및 규격': name,
        '단가': f"{unit:,}원",
        '수량': qty,
        '소계': f"{unit * qty:,}원",
        '역할': role[0] if role else ''
    } for cat, name, unit, qty, *role in budget
])
st.success(f"총 예상 제작 비용: 약 {total:,}원")
st.caption('※ 위 예산은 초기 설계 규모 산정을 위한 추정값입니다. 실제 가격은 구매처, 수량, 가공 방식, 배송비, 환율에 따라 달라질 수 있습니다.')

# Fusion 360 가이드
st.subheader('4. Fusion 360 기어 도면 & 초기 설계 가이드')
fusion_col1, fusion_col2 = st.columns([1.1, 1])
with fusion_col1:
    fig, center_dist, module_val, driven_teeth = draw_fusion_gear(best['ratio'], data['mass'])
    st.pyplot(fig, clear_figure=True)
with fusion_col2:
    st.markdown('''
**초기 스케치 가이드**

1. **중심 거리**  
   기어 모듈 `{module:.1f}` 기준, 두 축 간 거리는 **{center:.1f} mm**로 스케치하세요.

2. **조인트 설정**  
   Fusion 360에서 모터축과 바퀴축에 각각 `Revolute` 조인트를 적용한 뒤, `Motion Link`를 **360도 : {motion:.1f}도**로 설정하세요.

3. **3D 프린터 출력 팁**  
   구멍 공차는 도면보다 **+0.2 mm** 크게 잡으면 조립이 수월합니다.

4. **프레임 설계 순서**  
   바퀴 위치 → 축 위치 → 모터마운트 → 배터리 브라켓 → 보조기구부 순서로 배치하면 수정이 쉽습니다.
'''.format(module=module_val, center=center_dist, motion=360/best['ratio']))

# 스케치 및 설명
st.subheader('5. 초기 배치 스케치')
draw_sketch(data, part, best)

st.markdown('### 구조물과 장치의 유기적 역할 및 실행 프로세스')
st.markdown(process_description(data, part, best))

# 복사용 보고서
st.subheader('6. 테스트베드/보고서용 전체 내용 복사')
report_text = build_report_text(data, part, rows, calc, budget, total)
st.code(report_text, language='markdown')

# 브라우저 클립보드 복사 버튼
components.html(
    f"""
    <textarea id="copyText" style="position:absolute; left:-9999px; top:-9999px;">{report_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</textarea>
    <button onclick="navigator.clipboard.writeText(document.getElementById('copyText').value).then(() => alert('복사되었습니다.'))"
        style="background:#2563eb;color:white;border:none;border-radius:10px;padding:10px 16px;font-weight:700;cursor:pointer;">
        전체 내용 복사하기
    </button>
    """,
    height=55
)

