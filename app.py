import math
import io
import textwrap
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# =============================
# 페이지 설정
# =============================
st.set_page_config(page_title="모빌리티 구동계 초기 설계 도움 시스템", layout="wide")

PRESETS = {
    1: dict(scale='student', purpose='전동 킥보드형 퍼스널 모빌리티', mass=15, speed=15, unit='kmh', wheels=2, env='indoor', extra='경량 3D 프린팅 프레임, 접이식 구조'),
    2: dict(scale='research', purpose='스위피형 실내 청소로봇', mass=75, speed=1.2, unit='mps', wheels=2, env='indoor', extra='물탱크, 브러시, 저소음 감속기'),
    3: dict(scale='research', purpose='카고형 고하중 물류로봇', mass=365, speed=1.2, unit='mps', wheels=4, env='obstacle', extra='고하중 우레탄 바퀴, 자동 제동'),
    4: dict(scale='industry', purpose='초소형 전기차형 모빌리티', mass=562, speed=80, unit='kmh', wheels=4, env='normal', extra='강성 프레임, 독립 서스펜션'),
    5: dict(scale='research', purpose='산악 구조 보조 로봇', mass=50, speed=0.5, unit='mps', wheels=4, env='extreme', extra='궤도 트랙, 방수방진, 카메라'),
    6: dict(scale='industry', purpose='농업용 방제 로봇', mass=150, speed=1.0, unit='mps', wheels=4, env='extreme', extra='방제 펌프, 부식 방지 프레임'),
    7: dict(scale='student', purpose='FRC/대회용 공 수집 및 발사 로봇', mass=55, speed=2.0, unit='mps', wheels=4, env='indoor', extra='intake, feeder, shooter, waterwheel, 3D 프린팅 브라켓'),
    8: dict(scale='research', purpose='지능형 서비스 안내 로봇', mass=45, speed=1.0, unit='mps', wheels=2, env='indoor', extra='2D LiDAR, 카메라, LED 디스플레이'),
    9: dict(scale='research', purpose='궤도형 험지 탐사 로봇', mass=80, speed=0.7, unit='mps', wheels=4, env='extreme', extra='무한궤도, 장애물 극복, 센서 마스트'),
}

SCALE_OPTIONS = {
    'student': '학생용',
    'research': '연구용',
    'industry': '산업용',
}

ENV_OPTIONS = {
    'normal': '단순 이동 / 평지 중심',
    'indoor': '자율 이동 / 실내·완만한 경사',
    'obstacle': '장애물이 많은 지형',
    'extreme': '험한 지형 / 급경사·비포장',
}

UNIT_OPTIONS = {
    'mps': 'm/s',
    'kmh': 'km/h',
}

# =============================
# 유틸 함수
# =============================
def env_grade(env):
    return {'normal': 2, 'indoor': 8, 'obstacle': 15, 'extreme': 35}.get(env, 8)


def safe_float(value, default):
    try:
        if value is None or str(value).strip() == '':
            return default
        return float(str(value).strip())
    except Exception:
        return default


def safe_int(value, default):
    try:
        if value is None or str(value).strip() == '':
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def stars(n):
    n = max(1, min(5, int(n)))
    return '★' * n + '☆' * (5 - n)


def classify_parts(req_power, scale):
    """요구 동력과 제작 스케일에 따른 주요 부품 후보 및 단가."""
    # 학생용은 Fusion 360 + 3D 프린팅 기반 프레임을 우선 유도
    if scale == 'student' and req_power <= 220:
        if req_power <= 60:
            return dict(
                tier='학생용 소형', wheel_r=0.05, motor_rpm=4000, motor_nm=0.10,
                motor='Parvalux PBL42 Range BLDC · 24~48V · 4000rpm · 26~42W · 연속토크 0.06~0.10Nm 또는 IG32급 DC 기어드 모터', motor_cost=85000,
                gear='미스미 소모듈 평기어 M0.8~1.0 · 압력각 20° · C3604 황동/POM 또는 소형 타이밍 풀리', gear_cost=18000,
                wheel='100mm 우레탄/고무 로봇 바퀴 + Ø6mm SUS304 축 + 소형 베어링', wheel_cost=18000,
                control='Arduino/ESP32 제어보드 + 소형 DC/BLDC 드라이버 + 12~24V 배터리', control_cost=120000,
                frame='Fusion 360 설계 기반 PLA/PETG 3D 프린팅 차체·모터마운트·기어커버 + M3/M4 체결류', frame_cost=70000,
            )
        return dict(
            tier='학생용 중형', wheel_r=0.10, motor_rpm=3000, motor_nm=0.50,
            motor='Parvalux PBL60 Range BLDC · 24~48V · 3000rpm · 104~157W · 연속토크 0.33~0.50Nm 또는 775/550급 DC 모터', motor_cost=240000,
            gear='PGx42/GB28급 기어헤드 또는 미스미 평기어 M2.0 S45C + 타이밍벨트 보조 전달계', gear_cost=65000,
            wheel='200mm 솔리드 우레탄 바퀴 + Ø10mm S45C 축 + 플랜지 베어링', wheel_cost=55000,
            control='24V BLDC/DC 드라이버 2~4ch + 24V 10~20Ah 리튬 배터리 + 퓨즈', control_cost=420000,
            frame='Fusion 360 설계 기반 PETG/ABS/나일론-CF 3D 프린팅 섀시·보강 리브·모터마운트 + 열삽입 너트', frame_cost=180000,
        )

    if req_power <= 60 and scale != 'industry':
        return dict(
            tier='소형', wheel_r=0.05, motor_rpm=4000, motor_nm=0.10,
            motor='Parvalux PBL42 Range BLDC · 24~48V · 4000rpm · 26~42W · 연속토크 0.06~0.10Nm', motor_cost=85000,
            gear='미스미 소모듈 평기어 M0.8~1.0 · 압력각 20° · C3604 황동 또는 POM', gear_cost=18000,
            wheel='100mm 우레탄/고무 로봇 바퀴 + Ø6mm SUS304 축 + 소형 베어링', wheel_cost=18000,
            control='Arduino/ESP32 제어보드 + 소형 DC/BLDC 드라이버 + 12~24V 배터리', control_cost=120000,
            frame='PLA/PETG 3D 프린팅 브라켓 + 소형 프레임', frame_cost=90000,
        )
    if req_power <= 220 and scale != 'industry':
        return dict(
            tier='중소형', wheel_r=0.10, motor_rpm=3000, motor_nm=0.50,
            motor='Parvalux PBL60 Range BLDC · 24~48V · 3000rpm · 104~157W · 연속토크 0.33~0.50Nm', motor_cost=240000,
            gear='PGx42/GB28급 기어헤드 또는 미스미 평기어 M2.0 S45C', gear_cost=65000,
            wheel='200mm 솔리드 우레탄 바퀴 + Ø10mm S45C 축 + 플랜지 베어링', wheel_cost=55000,
            control='24V BLDC 드라이버 2~4ch + 24V 10~20Ah 리튬 배터리 + 퓨즈', control_cost=420000,
            frame='2020/3030 알루미늄 프로파일 프레임 + 3D프린팅 모터마운트', frame_cost=180000,
        )
    if req_power <= 650 or scale == 'research':
        return dict(
            tier='중형', wheel_r=0.12, motor_rpm=4000, motor_nm=1.40,
            motor='Parvalux PBL86 Range BLDC · 48V · 4000rpm · 419~586W · 연속토크 1.00~1.40Nm', motor_cost=480000,
            gear='Parvalux PGx70/PGx52 기어박스 또는 미스미 경제형 평기어 M3.0 · GB/T 10095 8등급', gear_cost=101396,
            wheel='250mm 고하중 우레탄 바퀴 + Ø15mm S45C 열처리 축 + 하우징 베어링', wheel_cost=95000,
            control='48V BLDC 드라이버 + 48V 20Ah 배터리팩 + BMS + 비상정지 스위치', control_cost=900000,
            frame='3030/4040 알루미늄 프로파일 또는 절곡 알루미늄 판재 섀시', frame_cost=350000,
        )
    return dict(
        tier='대형', wheel_r=0.25, motor_rpm=3000, motor_nm=8.00,
        motor='AC 서보모터 SD13/SD48급 또는 산업용 BLDC 서보 · 1kW 이상급 · 인버터 제어', motor_cost=1200000,
        gear='헬리컬/웜 감속기 또는 LIW/MWS급 고토크 기어헤드 · 28~45Nm급 이상', gear_cost=850000,
        wheel='13인치 이상 튜브/솔리드 타이어 + Ø20mm 이상 구동축 + 자동차형 베어링', wheel_cost=220000,
        control='서보 드라이브/인버터 + 48V~고전압 배터리팩 + BMS + 차단기', control_cost=3500000,
        frame='강철 사각파이프 용접 프레임 또는 주문제작 절곡 섀시', frame_cost=2200000,
    )


def aux_items(extra):
    e = extra.lower()
    items = []

    def has(*ks):
        return any(k.lower() in e for k in ks) or any(k in extra for k in ks)

    if has('intake', '인테이크'):
        items.append(('보조 기구부', 'Intake 흡입 롤러용 775/550급 DC 모터 또는 소형 BLDC + 고무 롤러 + 벨트', 95000, 1, '바닥의 공/물체를 로봇 내부로 끌어올림'))
    if has('feeder', '피더'):
        items.append(('보조 기구부', 'Feeder 이송용 서보모터/기어드 DC 모터 + 타이밍벨트 풀리', 80000, 1, '수집된 물체를 슈터나 저장부로 일정하게 공급'))
    if has('shooter', '슈터'):
        items.append(('보조 기구부', 'Shooter 고속 플라이휠용 BLDC/DC 모터 2개 + 플라이휠 + 모터 브라켓', 140000, 2, '고속 회전 휠로 공을 목표 방향으로 발사'))
    if has('waterwheel', '워터휠'):
        items.append(('보조 기구부', 'Waterwheel/색인 휠용 AC/BLDC 보조모터 + 원판형 휠', 120000, 1, '공 또는 물체의 방향과 공급 순서를 제어'))
    if has('lift', '리프트', '엘리베이터'):
        items.append(('보조 기구부', 'Lift 승강용 웜기어드 모터 + 리니어 가이드 + 랙기어', 160000, 1, '상하 이동 또는 높이 조절 기능 수행'))
    if has('lidar', '라이다', '카메라', '센서'):
        items.append(('센서/인식부', '2D LiDAR/카메라/초음파 센서 묶음 + 마운트', 220000, 1, '자율 이동과 장애물 인식'))
    if has('트랙', '궤도', 'track'):
        items.append(('주행 보강부', '소형 무한궤도 트랙 키트 또는 고무 트랙 벨트 세트', 180000, 2, '접지 면적을 늘려 험지 주행 안정성 향상'))
    return items


def analyze(data):
    scale = data['scale']
    mass = data['mass']
    speed = data['speed']
    unit = data['unit']
    wheels = max(1, int(data['wheels']))
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
        typ = '균형형' if r == center else ('속도형' if r < center else '토크형')
        reason = '목표 속도와 요구 토크의 균형이 가장 좋음' if typ == '균형형' else ('휠 RPM이 높아 빠른 주행에 유리하지만 토크 여유는 줄어듦' if typ == '속도형' else '감속비가 커서 등판·하중에 유리하지만 속도는 낮아짐')
        rows.append(dict(ratio=r, rpm=rpm, tq=tq, margin=margin, speed_err=speed_err, score=score, typ=typ, reason=reason, driven=20 * r))

    rows = sorted(rows, key=lambda x: x['score'], reverse=True)[:5]
    for i, row in enumerate(rows):
        row['stars'] = 5 - i

    calc = dict(speed_mps=speed_mps, speed_kmh=speed_mps * 3.6, grade=grade, req_power=req_power, req_tq=req_tq, req_rpm=req_rpm, motor_nm=motor_nm, req_force=req_force)
    return part, rows, calc

# =============================
# 스케치 생성 함수
# =============================
def _rounded_box(ax, xy, w, h, ec, lw=3.0, radius=18, fc='none'):
    ax.add_patch(
        patches.FancyBboxPatch(
            xy, w, h,
            boxstyle=f"round,pad=0.02,rounding_size={radius}",
            linewidth=lw, edgecolor=ec, facecolor=fc
        )
    )


def _label(ax, text, xy, xytext, color='#174a8b'):
    """그림 안 라벨은 영문만 사용해 Streamlit Cloud 한글 깨짐을 방지."""
    ax.annotate(
        text,
        xy=xy,
        xytext=xytext,
        arrowprops=dict(arrowstyle='->', color=color, lw=2.1),
        color=color,
        fontsize=10,
        fontweight='bold',
        ha='center',
        va='center',
        bbox=dict(boxstyle='round,pad=0.22', fc='white', ec=color, lw=1.3, alpha=0.96)
    )


def draw_initial_layout_sketch(data, part, best):
    """초기 배치 스케치 형식의 규칙 기반 도면. 외부 AI 없이 항상 생성됨."""
    fig, ax = plt.subplots(figsize=(11.5, 6.3))
    ax.set_xlim(0, 1200)
    ax.set_ylim(760, 0)
    ax.axis('off')
    ax.set_facecolor('white')

    frame_c = '#c7372f'   # 구조선: 붉은색
    device_c = '#315eea'  # 주행/제어 장치: 파란색
    aux_c = '#7a42e8'     # 보조기구: 보라색
    note_c = '#333333'
    lw = 4.0

    purpose = data['purpose'].lower()
    extra = data['extra'].lower()
    wheels = int(data['wheels'])

    # 제목부
    ax.text(55, 55, 'Initial layout sketch', fontsize=18, fontweight='bold', color=note_c)
    ax.text(55, 84, data['purpose'][:48], fontsize=11, color=note_c)

    # 유형 판정
    is_scooter = ('킥보드' in data['purpose']) or ('scooter' in purpose)
    is_car = ('전기차' in data['purpose']) or ('자동차' in data['purpose']) or ('차형' in data['purpose'])
    is_track = ('궤도' in data['extra']) or ('트랙' in data['extra']) or ('track' in extra)
    is_clean = ('청소' in data['purpose']) or ('브러시' in data['extra'])
    is_service = ('서비스' in data['purpose']) or ('안내' in data['purpose'])
    is_comp = ('frc' in purpose) or ('대회' in data['purpose']) or ('shooter' in extra) or ('intake' in extra)

    if is_scooter:
        # 킥보드형: 낮은 데크 + 앞 조향 핸들
        _rounded_box(ax, (270, 430), 540, 58, frame_c, lw, 26)
        ax.plot([720, 760, 785], [428, 230, 160], color=frame_c, lw=lw)
        ax.plot([740, 835], [170, 160], color=frame_c, lw=lw)
        wheel_pos = [(295, 520, 52), (785, 520, 52)]
        body_anchor = (540, 450)
        device_y = 385
    elif is_car:
        # 자동차형: 긴 하부 프레임 + 캐빈
        _rounded_box(ax, (195, 360), 760, 125, frame_c, lw, 28)
        ax.plot([340, 455, 690, 820], [360, 255, 255, 360], color=frame_c, lw=lw)
        ax.plot([455, 690], [255, 360], color=frame_c, lw=lw)
        wheel_pos = [(285, 530, 58), (850, 530, 58)]
        if wheels >= 6:
            wheel_pos.insert(1, (565, 540, 50))
        body_anchor = (555, 405)
        device_y = 315
    elif is_track:
        # 궤도형: 둥근 트랙 벨트 + 내부 보기륜
        _rounded_box(ax, (160, 435), 850, 145, frame_c, lw, 70)
        _rounded_box(ax, (235, 315), 700, 150, frame_c, lw, 28)
        wheel_pos = [(265, 515, 42), (510, 540, 36), (760, 515, 42)]
        body_anchor = (560, 380)
        device_y = 340
    elif is_service:
        # 서비스 로봇형: 세로 타워형 몸체
        _rounded_box(ax, (410, 250), 310, 300, frame_c, lw, 36)
        _rounded_box(ax, (455, 175), 220, 95, frame_c, lw, 24)
        wheel_pos = [(455, 585, 45), (675, 585, 45)]
        body_anchor = (565, 390)
        device_y = 320
    elif is_clean:
        # 청소 로봇형: 낮고 둥근 직사각형 + 하부 브러시
        _rounded_box(ax, (235, 350), 720, 165, frame_c, lw, 44)
        ax.add_patch(patches.Arc((590, 520), 340, 85, angle=0, theta1=0, theta2=180, color=frame_c, lw=lw))
        wheel_pos = [(335, 555, 48), (835, 555, 48)]
        body_anchor = (590, 410)
        device_y = 375
    else:
        # 일반 대회/탐구형: 예시 이미지 스타일의 단순 박스 프레임
        _rounded_box(ax, (210, 365), 760, 150, frame_c, lw, 30)
        ax.plot([290, 400, 720, 865], [365, 230, 230, 365], color=frame_c, lw=lw)
        ax.plot([400, 720], [230, 365], color=frame_c, lw=lw)
        wheel_pos = [(315, 550, 54), (850, 550, 54)]
        if wheels >= 6:
            wheel_pos.insert(1, (585, 558, 46))
        body_anchor = (590, 420)
        device_y = 350

    # 바퀴/보기륜
    for x, y, r in wheel_pos:
        ax.add_patch(patches.Circle((x, y), r, fill=False, edgecolor=frame_c, lw=lw))
        ax.add_patch(patches.Circle((x, y), r * 0.45, fill=False, edgecolor=frame_c, lw=2.7))

    # 주행 모터 + 감속기
    mx = wheel_pos[0][0] - 70
    my = wheel_pos[0][1] - 85
    _rounded_box(ax, (mx, my), 110, 50, device_c, 3.2, 10)
    ax.add_patch(patches.Circle((mx + 132, my + 25), 24, fill=False, edgecolor=device_c, lw=3.2))
    _label(ax, 'Drive motor', (mx + 50, my + 25), (105, 645), device_c)
    _label(ax, f'{best["ratio"]}:1 gear', (mx + 132, my + 25), (355, 650), frame_c)

    # 배터리/제어기
    bx, by = body_anchor[0] - 85, body_anchor[1] - 10
    _rounded_box(ax, (bx, by), 170, 62, device_c, 3.2, 10)
    _label(ax, 'Battery / controller', (bx + 85, by + 31), (585, 690), device_c)

    # 센서
    if any(k in extra for k in ['lidar', '라이다', '카메라', '센서']) or '서비스' in data['purpose'] or '안내' in data['purpose']:
        ax.add_patch(patches.Circle((body_anchor[0], device_y - 95), 28, fill=False, edgecolor=aux_c, lw=3.2))
        _label(ax, 'Sensor', (body_anchor[0], device_y - 95), (1035, 150), aux_c)

    # 보조 기구부: 본체 밖에 배치해 겹침 방지
    if 'intake' in extra or '인테이크' in data['extra']:
        _rounded_box(ax, (955, 405), 135, 86, aux_c, 3.2, 12)
        _label(ax, 'Intake', (1020, 448), (1040, 610), aux_c)
    if 'feeder' in extra or '피더' in data['extra']:
        _rounded_box(ax, (345, 275), 135, 74, aux_c, 3.2, 12)
        _label(ax, 'Feeder', (410, 312), (120, 290), aux_c)
    if 'shooter' in extra or '슈터' in data['extra']:
        _rounded_box(ax, (690, 145), 155, 94, aux_c, 3.2, 12)
        _label(ax, 'Shooter motors', (768, 190), (945, 105), aux_c)
    if 'waterwheel' in extra or '워터휠' in data['extra']:
        ax.add_patch(patches.Circle((650, 315), 43, fill=False, edgecolor=aux_c, lw=3.2))
        _label(ax, 'Index wheel', (692, 315), (1015, 315), aux_c)
    if 'lift' in extra or '리프트' in data['extra'] or '엘리베이터' in data['extra']:
        _rounded_box(ax, (160, 205), 80, 185, aux_c, 3.2, 14)
        _label(ax, 'Lift motor', (200, 270), (110, 120), aux_c)

    # 하단 메모 박스
    ax.text(55, 715, 'Sketch note: red = frame/body, blue = drive system, purple = auxiliary mechanisms', fontsize=10, color=note_c)

    st.pyplot(fig, clear_figure=True)

# =============================
# 설명 생성
# =============================
def process_description(data, part, rows, calc):
    best = rows[0] if rows else {'ratio': '-', 'rpm': 0, 'tq': 0}
    extra = data['extra'].lower()
    lines = []
    lines.append(f"이 초기 배치 스케치는 '{data['purpose']}'의 기능을 완성 외형이 아니라 장치 배치 관점에서 정리한 것입니다. 붉은색 선은 차체·프레임의 기본 뼈대, 파란색 박스는 주행 구동부와 배터리/제어기, 보라색 박스는 보조 기구부를 의미합니다.")
    lines.append(f"주행 과정에서는 배터리와 제어기가 주행 모터에 전력을 공급하고, 모터 회전은 감속기와 기어비 {best['ratio']}:1 후보를 거쳐 바퀴축으로 전달됩니다. 이때 감속비가 적용되면서 휠 RPM은 약 {best['rpm']:.1f}RPM 수준으로 조정되고, 휠 토크는 약 {best['tq']:.2f}Nm로 증폭됩니다.")
    lines.append("프레임은 단순히 외형을 만드는 부품이 아니라 모터 마운트, 축 베어링, 배터리 고정 위치, 보조 기구의 기준 위치를 잡아주는 기준 구조물입니다. 따라서 Fusion 360에서 처음 설계할 때는 바퀴축 위치와 모터축 위치를 먼저 잡고, 그 사이에 기어 중심거리와 모터 마운트 구멍을 배치하는 방식이 안정적입니다.")
    if 'intake' in extra or '인테이크' in data['extra']:
        lines.append("인테이크가 포함된 경우, 전면 흡입 롤러가 물체를 끌어들이고 프레임 내부의 이송 경로로 넘기는 역할을 합니다.")
    if 'feeder' in extra or '피더' in data['extra']:
        lines.append("피더가 포함된 경우, 인테이크로 들어온 물체를 저장부 또는 슈터 쪽으로 일정한 간격으로 공급하여 전체 동작이 끊기지 않도록 합니다.")
    if 'shooter' in extra or '슈터' in data['extra']:
        lines.append("슈터가 포함된 경우, 별도의 고속 모터와 플라이휠이 필요하며 주행 구동부와 전원 용량을 공유하므로 배터리 방전율과 모터 드라이버 허용 전류를 함께 검토해야 합니다.")
    if 'waterwheel' in extra or '워터휠' in data['extra']:
        lines.append("워터휠 또는 색인 휠은 여러 물체가 한꺼번에 들어오는 상황에서 공급 순서와 방향을 정렬하는 역할을 합니다.")
    if '궤도' in data['extra'] or '트랙' in data['extra'] or 'track' in extra:
        lines.append("궤도형 구조는 접지 면적을 넓혀 험지 안정성을 높이는 대신, 회전 저항과 제작 난도가 증가하므로 모터 여유 토크와 프레임 강성을 더 크게 잡아야 합니다.")
    return "\n\n".join(lines)


def fusion_guide(data, rows):
    if not rows:
        return "기어 후보가 없어 Fusion 360 가이드를 생성할 수 없습니다."
    best = rows[0]
    module = 1.0 if data['mass'] <= 60 else 2.0
    center_distance = ((20 + best['driven']) * module) / 2
    motion_link_deg = 360 / best['ratio']
    return f"""1. 중심 거리: 기어 모듈 {module:.1f} 기준, 두 축 간 거리는 {center_distance:.1f}mm로 스케치하세요.
2. 조인트(Fusion 360): 모터축과 바퀴축에 Revolute 조인트를 적용한 뒤 Motion Link를 360도 : {motion_link_deg:.1f}도로 설정하세요.
3. 3D 프린터 출력 팁: 축 구멍과 베어링 삽입부는 도면보다 +0.2mm 정도 크게 잡으면 조립이 수월합니다.
4. 학생용 제작 팁: PLA는 출력이 쉽지만 충격에는 약하므로, 모터마운트와 축 지지대는 PETG/ABS/나일론-CF 또는 두꺼운 리브 구조를 권장합니다.
5. 먼저 바퀴축 위치, 모터축 위치, 배터리 위치를 고정한 뒤 보조기구부를 얹으면 설계 변경이 줄어듭니다."""


def draw_fusion_gear_canvas(data, rows):
    if not rows:
        return
    best = rows[0]
    module = 1.0 if data['mass'] <= 60 else 2.0
    drive_teeth = 20
    driven_teeth = best['driven']
    r1 = drive_teeth * module / 2
    r2 = driven_teeth * module / 2
    center = r1 + r2

    fig, ax = plt.subplots(figsize=(6.3, 3.8))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_facecolor('white')

    ax.add_patch(patches.Circle((0, 0), r1, fill=False, linestyle='--', linewidth=2.4, edgecolor='#315eea'))
    ax.add_patch(patches.Circle((center, 0), r2, fill=False, linestyle='--', linewidth=2.4, edgecolor='#c7372f'))
    ax.plot([0, center], [0, 0], color='#555555', linestyle='-.', linewidth=1.6)
    ax.plot(0, 0, 'ko', markersize=4)
    ax.plot(center, 0, 'ko', markersize=4)
    ax.text(0, -r1 - 10, 'Motor gear\n20T', ha='center', va='top', color='#315eea', fontsize=10)
    ax.text(center, -r2 - 10, f'Wheel gear\n{driven_teeth}T', ha='center', va='top', color='#c7372f', fontsize=10)
    ax.text(center / 2, 8, f'Center distance: {center:.1f} mm', ha='center', fontsize=10, color='#333333')
    ax.set_xlim(-r1 - 25, center + r2 + 25)
    ax.set_ylim(-max(r1, r2) - 35, max(r1, r2) + 25)
    st.pyplot(fig, clear_figure=True)


def build_report_text(data, part, rows, calc, budget, total):
    gear_lines = []
    for i, r in enumerate(rows, 1):
        gear_lines.append(f"{i}위 {stars(r['stars'])}: {r['ratio']}:1, 20T:{r['driven']}T, RPM {r['rpm']:.1f}, 토크 {r['tq']:.2f}Nm, {r['typ']} - {r['reason']}")
    budget_lines = []
    for cat, name, unit, qty, *role in budget:
        budget_lines.append(f"- {cat}: {name} / 단가 {unit:,}원 x {qty} = {unit * qty:,}원")
    return f"""[모빌리티 구동계 초기 설계 요약]
용도: {data['purpose']}
스케일: {SCALE_OPTIONS.get(data['scale'], data['scale'])}
질량: {data['mass']}kg
목표 속도: {data['speed']} {UNIT_OPTIONS.get(data['unit'], data['unit'])}
구동 바퀴 수: {data['wheels']}개
운행 환경: {ENV_OPTIONS.get(data['env'], data['env'])}
기타 요구사항: {data['extra']}

[물리 모델 결과]
요구 동력: {calc['req_power']:.0f}W
바퀴당 요구 토크: {calc['req_tq']:.2f}Nm
필요 휠 RPM: {calc['req_rpm']:.1f}RPM
추천 모터 후보: {part['motor']}

[기어비 후보]
{chr(10).join(gear_lines)}

[예산안]
총 예상 제작 비용: 약 {total:,}원
{chr(10).join(budget_lines)}

[Fusion 360 초기 설계 가이드]
{fusion_guide(data, rows)}

[구조물과 장치의 유기적 역할]
{process_description(data, part, rows, calc)}
"""

# =============================
# 화면 구성
# =============================
st.title("모빌리티 구동계 초기 설계 도움 시스템")
st.caption("제작자가 탐구와 설계를 시작할 수 있도록 물리 계산 기반 초기 후보안, 예산안, 기어비, 초기 배치 스케치를 제공하는 보조 도구입니다.")

with st.sidebar:
    st.header("설정")
    option_list = ["직접 입력"] + [f"{k}. {v['purpose']} ({v['mass']}kg)" for k, v in PRESETS.items()]
    selected_option = st.selectbox("빠른 설정 또는 직접 입력", option_list, index=0)

    # 직접 입력은 비워두고, 프리셋은 검은 글씨 기본값으로 표시하되 수정 가능
    if selected_option == "직접 입력":
        default = dict(scale='', purpose='', mass='', speed='', unit='', wheels='', env='', extra='')
        st.info("직접 입력은 빈칸으로 시작합니다. 비워둔 항목은 내부 기본값으로 계산됩니다.")
    else:
        preset_key = int(selected_option.split('.')[0])
        default = PRESETS[preset_key].copy()
        st.info("프리셋 값이 입력란에 불러와졌습니다. 필요한 부분은 직접 수정할 수 있습니다.")

    # scale selectbox: 직접 입력 시 안내용 빈 옵션 포함
    scale_keys = ['', 'student', 'research', 'industry']
    scale_labels = {
        '': '선택 안 함',
        'student': '학생용',
        'research': '연구용',
        'industry': '산업용',
    }
    scale_index = scale_keys.index(default.get('scale', '')) if default.get('scale', '') in scale_keys else 0
    scale = st.selectbox("1. 로봇 제작 스케일", scale_keys, index=scale_index, format_func=lambda x: scale_labels[x])

    purpose = st.text_input("2. 목표 모빌리티의 용도", value=str(default.get('purpose', '')), placeholder="예: FRC/대회용 공 수집 및 발사 로봇")
    mass_raw = st.text_input("3. 예상 총 질량 (kg)", value=str(default.get('mass', '')), placeholder="예: 35")
    speed_raw = st.text_input("4. 목표 주행 속도", value=str(default.get('speed', '')), placeholder="예: 1.5")

    unit_keys = ['', 'mps', 'kmh']
    unit_labels = {'': '선택 안 함', 'mps': 'm/s', 'kmh': 'km/h'}
    unit_index = unit_keys.index(default.get('unit', '')) if default.get('unit', '') in unit_keys else 0
    unit = st.selectbox("5. 속도 단위", unit_keys, index=unit_index, format_func=lambda x: unit_labels[x])

    wheels_raw = st.text_input("6. 구동 바퀴 수", value=str(default.get('wheels', '')), placeholder="예: 4")

    env_keys = ['', 'normal', 'indoor', 'obstacle', 'extreme']
    env_labels = {'': '선택 안 함', **ENV_OPTIONS}
    env_index = env_keys.index(default.get('env', '')) if default.get('env', '') in env_keys else 0
    env = st.selectbox("7. 로봇 운행 환경", env_keys, index=env_index, format_func=lambda x: env_labels[x])

    extra = st.text_area(
        "8. 기타 요구사항",
        value=str(default.get('extra', '')),
        placeholder="예: intake, feeder, shooter, waterwheel, 카메라, 방수방진 등\n상세할수록 모빌리티가 구체화됩니다.",
        height=100,
    )

    run = st.button("설계 데이터 및 스케치 생성하기", type="primary", use_container_width=True)

# 입력값 기본 처리: 프리셋은 불러온 값을 수정 가능, 직접 입력은 빈값이면 기본값
base_data = dict(
    scale=scale if scale else 'student',
    purpose=purpose.strip() if purpose.strip() else '학생용 이동 로봇',
    mass=safe_float(mass_raw, 35.0),
    speed=safe_float(speed_raw, 1.5),
    unit=unit if unit else 'mps',
    wheels=safe_int(wheels_raw, 4),
    env=env if env else 'indoor',
    extra=extra.strip() if extra.strip() else '없음',
)

if run:
    data = base_data
    part, rows, calc = analyze(data)

    st.subheader("1. 물리 모델 분석 결과")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("요구 동력", f"{calc['req_power']:.0f} W")
    col2.metric("바퀴당 요구 토크", f"{calc['req_tq']:.2f} Nm")
    col3.metric("필요 휠 RPM", f"{calc['req_rpm']:.1f} RPM")
    col4.metric("적용 경사각", f"{calc['grade']}°")
    st.info(f"**추천 모터 후보:** {part['motor']}  \\n**권장 기준 토크:** {calc['motor_nm']:.2f} Nm  \\n**제작 체급:** {part['tier']}")

    st.subheader("2. 기어비 후보 분석")
    st.table([
        {
            "순위/추천도": f"{i}위 {stars(r['stars'])}",
            "기어비": f"{r['ratio']}:1",
            "구동:피동 기어": f"20T : {r['driven']}T",
            "예상 휠 RPM": f"{r['rpm']:.1f}",
            "예상 휠 토크": f"{r['tq']:.2f} Nm",
            "유형": r['typ'],
            "추천도 선정 이유": r['reason'],
        } for i, r in enumerate(rows, 1)
    ])
    st.caption("별점은 목표 휠 RPM과의 차이, 요구 토크 대비 여유, 감속비 특성을 함께 고려해 정렬한 상대 추천도입니다.")

    st.subheader("3. 정밀 예산안")
    budget = [
        ('주행 구동부', part['motor'], part['motor_cost'], data['wheels']),
        ('주행 구동부', part['gear'], part['gear_cost'], data['wheels']),
        ('바퀴/축/베어링', part['wheel'], part['wheel_cost'], data['wheels']),
        ('제어/전원부', part['control'], part['control_cost'], 1),
        ('주요 구성 형체', part['frame'], part['frame_cost'], 1),
    ] + aux_items(data['extra'])

    total = sum(x[2] * x[3] for x in budget)
    st.table([
        {
            "분류": cat,
            "상세 품명 및 규격": name,
            "단가": f"{unit_price:,}원",
            "수량": qty,
            "소계": f"{unit_price * qty:,}원",
            "역할": role[0] if role else "초기 제작 구성품",
        }
        for cat, name, unit_price, qty, *role in budget
    ])
    st.success(f"총 예상 제작 비용: 약 {total:,}원")
    st.caption("예산은 초기 후보안 산정을 위한 추정값입니다. 실제 구매처, 재고, 배송비, 가공비, 출력 실패율에 따라 달라질 수 있습니다.")

    st.subheader("4. Fusion 360 기어 도면 & 초기 설계 가이드")
    cad_col1, cad_col2 = st.columns([1, 1])
    with cad_col1:
        draw_fusion_gear_canvas(data, rows)
    with cad_col2:
        st.markdown("**초기 스케치 가이드**")
        st.text(fusion_guide(data, rows))

    st.subheader("5. 초기 구상 설계 이미지")
    draw_initial_layout_sketch(data, part, rows[0])

    st.markdown("**그림 라벨 한국어 설명**")
    st.markdown(
        "- **Drive motor**: 주행 모터입니다. 배터리 전력을 회전 운동으로 바꾸는 핵심 장치입니다.\n"
        "- **Gear / Gearbox**: 감속기 또는 기어부입니다. 회전 속도를 낮추고 바퀴 토크를 키웁니다.\n"
        "- **Battery / controller**: 배터리와 제어기입니다. 모터 드라이버, 전원 분배, 센서 신호 처리를 담당합니다.\n"
        "- **Intake / Feeder / Shooter / Index wheel / Lift**: 기타 요구사항에 따라 추가되는 보조 구동 장치입니다."
    )

    st.markdown("**구조물과 장치들의 유기적 역할 및 실행 프로세스**")
    st.write(process_description(data, part, rows, calc))

    st.subheader("6. 테스트베드/보고서용 전체 내용 복사")
    report_text = build_report_text(data, part, rows, calc, budget, total)
    st.code(report_text, language="text")
    st.download_button(
        label="요약 내용을 txt 파일로 다운로드",
        data=report_text.encode('utf-8'),
        file_name="mobility_design_summary.txt",
        mime="text/plain",
        use_container_width=True,
    )
else:
    st.info("왼쪽 사이드바에서 직접 입력하거나 프리셋을 선택한 뒤, 값을 확인·수정하고 버튼을 눌러 설계안을 생성하세요.")
    st.markdown(
        """
        ### 사용 방법
        1. 프리셋을 선택하면 값이 입력란에 검은 글씨로 채워집니다. 필요한 항목은 직접 수정할 수 있습니다.  
        2. 직접 입력을 선택하면 입력란이 비어 있습니다. 비워둔 항목은 내부 기본값으로 계산됩니다.  
        3. 기타 요구사항에 `intake`, `feeder`, `shooter`, `waterwheel`, `궤도`, `카메라` 등을 적으면 스케치와 예산안에 반영됩니다.  
        4. 결과는 초기 설계 후보안이며, 실제 제작 전 강도·발열·전류·안전 검증이 필요합니다.
        """
    )

