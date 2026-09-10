
import math
import textwrap
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# =============================
# 페이지 설정
# =============================
st.set_page_config(page_title="모빌리티 구동계 초기 설계 도움 시스템", layout="wide")

# =============================
# 프리셋 데이터
# =============================
PRESETS = {
    1: dict(scale='student', purpose='전동 킥보드형 퍼스널 모빌리티', mass=15, speed=15, unit='kmh', wheels=2, env='indoor', extra='경량 차체, 접이식 구조, 손잡이 조향'),
    2: dict(scale='research', purpose='스위피형 실내 청소로봇', mass=75, speed=1.2, unit='mps', wheels=2, env='indoor', extra='물탱크, 브러시, 저소음 감속기'),
    3: dict(scale='research', purpose='카고형 고하중 물류로봇', mass=365, speed=1.2, unit='mps', wheels=4, env='obstacle', extra='고하중 우레탄 바퀴, 자동 제동'),
    4: dict(scale='industry', purpose='초소형 전기차형 모빌리티', mass=562, speed=80, unit='kmh', wheels=4, env='normal', extra='강성 프레임, 독립 서스펜션'),
    5: dict(scale='research', purpose='산악 구조 보조 로봇', mass=50, speed=0.5, unit='mps', wheels=4, env='extreme', extra='궤도 트랙, 방수방진, 카메라'),
    6: dict(scale='industry', purpose='농업용 방제 로봇', mass=150, speed=1.0, unit='mps', wheels=4, env='extreme', extra='방제 펌프, 부식 방지 프레임'),
    7: dict(scale='student', purpose='FRC/대회용 공 수집 및 발사 로봇', mass=55, speed=2.0, unit='mps', wheels=4, env='indoor', extra='intake, feeder, shooter, waterwheel, 3D 프린팅 브라켓'),
    8: dict(scale='research', purpose='지능형 서비스 안내 로봇', mass=45, speed=1.0, unit='mps', wheels=2, env='indoor', extra='2D LiDAR, 카메라, LED 디스플레이'),
    9: dict(scale='research', purpose='궤도형 험지 탐사 로봇', mass=80, speed=0.7, unit='mps', wheels=4, env='extreme', extra='무한궤도, 장애물 극복, 센서 마스트'),
}

SCALE_LABEL = {
    'student': '학생용 / 공모전·탐구용',
    'research': '연구용 / 실험·프로토타입용',
    'industry': '산업용 / 고하중·전문 제작용',
}

ENV_LABEL = {
    'normal': '단순 이동 / 평지 중심',
    'indoor': '실내 자율 이동 / 완만한 문턱·램프',
    'obstacle': '장애물이 많은 지형 / 요철·배관·턱',
    'extreme': '험한 지형 / 급경사·비포장·산악',
}

# =============================
# 기본 함수
# =============================
def env_grade(env):
    return {'normal': 2, 'indoor': 8, 'obstacle': 15, 'extreme': 35}.get(env, 8)


def stars(n):
    n = max(1, min(5, int(n)))
    return '★' * n + '☆' * (5 - n)


def safe_float(value, default):
    try:
        if value is None or str(value).strip() == '':
            return default
        return float(value)
    except Exception:
        return default


def safe_int(value, default):
    try:
        if value is None or str(value).strip() == '':
            return default
        return int(float(value))
    except Exception:
        return default


# =============================
# 부품 분류 및 예산 DB
# =============================
def classify_parts(req_power, scale):
    """
    첨부된 모터 종류 자료 기반으로 체급별 후보를 넓게 제공한다.
    가격은 초기 예산 추정용 단가이며, 실제 구매처·수량·배송비·가공비에 따라 변동될 수 있다.
    """
    # 학생용은 외형/프레임을 알루미늄 프로파일보다 Fusion 360 + 3D 프린팅 중심으로 유도
    if scale == 'student':
        if req_power <= 60:
            return dict(
                tier='학생용 소형', wheel_r=0.05, motor_rpm=4000, motor_nm=0.10,
                motor='Parvalux PBL42 Range BLDC · 24~48V · 4000rpm · 26~42W · 연속토크 0.06~0.10Nm', motor_cost=85000,
                motor_options=[
                    '1순위: Parvalux PBL42 BLDC · 26~42W · 4000rpm · 24~48V · 소형 주행축/가벼운 로봇',
                    '대안: IG32/37급 12~24V DC 기어드 모터 · 엔코더형 · 저가형 학생 제작',
                    '대안: 소형 DC 서보모터 · 위치 제어가 필요한 조향/소형 암 구동'
                ],
                gear='미스미 소모듈 평기어 M0.8~1.0 · 압력각 20° · 황동/C3604 또는 POM', gear_cost=18000,
                gear_options=[
                    '평기어: 모터축과 바퀴축이 평행할 때 가장 단순하고 제작 쉬움',
                    '타이밍벨트 풀리: 소음이 작고 3D 프린팅 브라켓과 조합하기 쉬움',
                    '소형 유성감속기: 공간이 좁고 큰 감속비가 필요할 때 사용'
                ],
                wheel='100mm 이하 우레탄/고무 로봇 바퀴 + Ø6mm SUS304 축 + 소형 베어링', wheel_cost=18000,
                control='Arduino/ESP32 제어보드 + 소형 DC/BLDC 드라이버 + 12~24V 배터리', control_cost=120000,
                frame='Fusion 360 설계 PLA/PETG 3D 프린팅 차체·모터마운트·기어커버 + M3/M4 체결류', frame_cost=75000,
                frame_basis='PLA/PETG 필라멘트 1~2롤, 노즐/서포트 여유분, M3/M4 볼트·너트·열삽입 너트 기준'
            )
        return dict(
            tier='학생용 중형', wheel_r=0.10, motor_rpm=3000, motor_nm=0.50,
            motor='Parvalux PBL60 Range BLDC · 24~48V · 3000rpm · 104~157W · 연속토크 0.33~0.50Nm', motor_cost=240000,
            motor_options=[
                '1순위: Parvalux PBL60 BLDC · 104~157W · 3000rpm · 대회용 중형 주행축',
                '대안: Parvalux PBL70 BLDC · 363~415W · 4500rpm · 빠른 주행/고출력 요구',
                '대안: DC 서보모터 · 기동토크가 크고 회전 방향 반전이 쉬운 구조',
                '대안: 775/550급 DC 모터 + 감속기 · 슈터/인테이크 보조 구동에 적합'
            ],
            gear='PGx42/GB28급 기어헤드 또는 미스미 평기어 M2.0 S45C', gear_cost=65000,
            gear_options=[
                'PGx42 계열: 2.3~11.3Nm급 제어 토크 범위의 소형 기어헤드 후보',
                'GB28 계열: 약 5Nm급 기어박스 후보',
                'M2.0 평기어: 학생용 3D 프린팅 브라켓과 금속축 조합에 적합'
            ],
            wheel='200mm 솔리드 우레탄 바퀴 + Ø10mm S45C 축 + 플랜지 베어링', wheel_cost=55000,
            control='24V BLDC 드라이버 2~4ch + 24V 10~20Ah 리튬 배터리 + 퓨즈', control_cost=420000,
            frame='Fusion 360 설계 PETG/ABS/나일론-CF 3D 프린팅 섀시·모터마운트·보강 리브 + 열삽입 너트', frame_cost=160000,
            frame_basis='PETG/ABS/나일론-CF 필라멘트 2~4롤, 실패 출력 여유분, 열삽입 너트·볼트·베어링 하우징 기준'
        )

    # 연구용
    if req_power <= 60:
        return dict(
            tier='연구용 소형', wheel_r=0.05, motor_rpm=4000, motor_nm=0.10,
            motor='Parvalux PBL42 Range BLDC · 24~48V · 4000rpm · 26~42W · 연속토크 0.06~0.10Nm', motor_cost=85000,
            motor_options=[
                'Parvalux PBL42 BLDC · 26~42W · 소형 자율주행 플랫폼',
                'SD41 AC 모터 · 10~25W · 1400~3400rpm · 저출력 AC 구동 실험',
                'DC 서보모터 · 저가형 방향 제어 및 저속 구동 실험'
            ],
            gear='미스미 소모듈 평기어 M0.8~1.0 또는 소형 유성감속기', gear_cost=18000,
            gear_options=['평기어', '타이밍벨트', '소형 유성감속기'],
            wheel='100mm 우레탄 바퀴 + Ø6mm 축 + 소형 베어링', wheel_cost=18000,
            control='ESP32/STM32 제어보드 + BLDC/DC 드라이버 + 배터리', control_cost=160000,
            frame='소형 알루미늄 판재 또는 3D 프린팅 브라켓 혼합 차체', frame_cost=110000,
            frame_basis='소형 판재, 출력 브라켓, 체결류 포함'
        )
    if req_power <= 650:
        return dict(
            tier='연구용 중형', wheel_r=0.12, motor_rpm=4000, motor_nm=1.40,
            motor='Parvalux PBL86 Range BLDC · 48V · 4000rpm · 419~586W · 연속토크 1.00~1.40Nm', motor_cost=480000,
            motor_options=[
                '1순위: Parvalux PBL86 BLDC · 419~586W · 48V · 4000rpm · 중형 AGV/물류형 주행',
                '대안: Parvalux PBL70 BLDC · 363~415W · 48V · 고속 소형 물류로봇',
                '대안: AC 서보모터 SD13 · 100~150W · 1400~3400rpm · 0.42~0.85Nm',
                '대안: AC 모터 SD48 · 55~250W · 0.53~1.30Nm · 장시간 운전 후보'
            ],
            gear='Parvalux PGx70/PGx52 기어박스 또는 미스미 경제형 평기어 M3.0 · GB/T 10095 8등급', gear_cost=101396,
            gear_options=[
                'PGx70: 10~30Nm급 제어 토크 후보',
                'PGx52: 5~30Nm급 제어 토크 후보',
                '미스미 M3.0 평기어: 표준가 약 101,396원 예시 자료 기반',
                '웜기어: 큰 감속비와 역구동 억제가 필요한 리프트/브레이크 구조'
            ],
            wheel='250mm 고하중 우레탄 바퀴 + Ø15mm S45C 열처리 축 + 하우징 베어링', wheel_cost=95000,
            control='48V BLDC 드라이버 + 48V 20Ah 배터리팩 + BMS + 비상정지 스위치', control_cost=900000,
            frame='3030/4040 알루미늄 프로파일 또는 절곡 알루미늄 판재 섀시', frame_cost=350000,
            frame_basis='알루미늄 프로파일/판재, 브라켓, 체결류, 모터 마운트 포함'
        )
    return dict(
        tier='연구용 대형', wheel_r=0.18, motor_rpm=3000, motor_nm=4.50,
        motor='산업용 BLDC/AC 서보 · 750W~1kW급 · 고하중 연구 플랫폼', motor_cost=850000,
        motor_options=[
            'AC 서보모터 SD13/SD48급 확장형 · 인버터 제어',
            '산업용 BLDC 서보 · 750W~1kW · 고하중 구동',
            'PBL86 + 고토크 기어헤드 조합 · 중대형 연구용'
        ],
        gear='PGx70/LIW/MWS급 고토크 기어헤드 또는 헬리컬 감속기', gear_cost=450000,
        gear_options=['LIW 28~45Nm급', 'MWS 9~45Nm급', '헬리컬 감속기', '웜기어 감속기'],
        wheel='300mm 이상 고하중 바퀴 + Ø20mm 이상 축 + 하우징 베어링', wheel_cost=150000,
        control='서보 드라이브/48V 대용량 배터리/BMS/차단기', control_cost=1800000,
        frame='절곡 알루미늄 또는 강철 보강 섀시', frame_cost=800000,
        frame_basis='절곡/가공/용접 의뢰 및 보강 브라켓 포함'
    )

    # 산업용
    # unreachable safeguard


def classify_industry_parts(req_power):
    return dict(
        tier='산업용 대형', wheel_r=0.25, motor_rpm=3000, motor_nm=8.00,
        motor='AC 서보모터 SD13/SD48급 또는 산업용 BLDC 서보 · 1kW 이상급 · 인버터 제어', motor_cost=1200000,
        motor_options=[
            '1순위: AC 서보모터 SD48 계열 · 55~250W 자료 기반을 상위 서보 시스템으로 확장 적용',
            '대안: 산업용 BLDC 서보 1kW 이상급 · 고하중 구동축',
            '대안: AC 서보 + 인버터 조합 · 장시간 운전과 정밀 속도 제어',
            '대안: EV형 구동 모터 + 감속기 · 초소형 전기차형 플랫폼'
        ],
        gear='헬리컬/웜 감속기 또는 LIW/MWS급 고토크 기어헤드 · 28~45Nm급 이상', gear_cost=850000,
        gear_options=[
            'LIW 범위: 28~45Nm급 고토크 기어헤드 후보',
            'MWS 범위: 9~45Nm급 후보',
            '헬리컬 기어: 엇갈리는 축과 높은 전달 안정성',
            '웜 기어: 큰 감속비와 역구동 억제가 필요한 구조'
        ],
        wheel='13인치 이상 튜브/솔리드 타이어 + Ø20mm 이상 구동축 + 자동차형 베어링', wheel_cost=220000,
        control='서보 드라이브/인버터 + 48V~고전압 배터리팩 + BMS + 차단기', control_cost=3500000,
        frame='강철 사각파이프 용접 프레임 또는 주문제작 절곡 섀시', frame_cost=2200000,
        frame_basis='강철 사각파이프, 용접, 절곡, 도장, 대형 체결류, 안전커버 포함'
    )


def get_parts(req_power, scale):
    if scale == 'industry':
        return classify_industry_parts(req_power)
    return classify_parts(req_power, scale)


# =============================
# 보조 구동부 분석
# =============================
def aux_items(extra):
    e = extra.lower()
    items = []

    def has(*ks):
        return any(k.lower() in e or k in extra for k in ks)

    if has('intake', '인테이크'):
        items.append(('보조 기구부', 'Intake 흡입 롤러용 775/550급 DC 모터 또는 소형 BLDC + 고무 롤러 + 벨트', 95000, 1, '바닥의 공/물체를 로봇 내부로 끌어올림'))
    if has('feeder', '피더'):
        items.append(('보조 기구부', 'Feeder 이송용 서보모터/기어드 DC 모터 + 타이밍벨트 풀리', 80000, 1, '수집된 물체를 슈터나 저장부로 일정하게 공급'))
    if has('shooter', '슈터'):
        items.append(('보조 기구부', 'Shooter 고속 플라이휠용 BLDC/DC 모터 2개 + 플라이휠 + 모터 브라켓', 140000, 2, '고속 회전 휠로 공을 목표 방향으로 발사'))
    if has('waterwheel', '워터휠', 'index', '인덱스'):
        items.append(('보조 기구부', 'Waterwheel/색인 휠용 AC/BLDC 보조모터 + 원판형 휠', 120000, 1, '공 또는 물체의 방향과 공급 순서를 제어'))
    if has('lift', '리프트', '엘리베이터'):
        items.append(('보조 기구부', 'Lift 승강용 웜기어드 모터 + 리니어 가이드 + 랙기어', 160000, 1, '상하 이동 또는 높이 조절 기능 수행'))
    if has('brush', '브러시', '청소'):
        items.append(('보조 기구부', '청소 브러시용 저속 DC 기어드 모터 + 브러시 롤러', 90000, 1, '바닥 이물질을 쓸어 담거나 세척부로 전달'))
    if has('pump', '펌프', '방제'):
        items.append(('보조 기구부', '방제/워터펌프 모듈 + 분사 노즐 + 릴레이 제어부', 180000, 1, '액체를 흡입하여 노즐로 분사'))
    if has('lidar', '라이다', '카메라', '센서', 'camera'):
        items.append(('센서/인식부', '2D LiDAR/카메라/초음파 센서 묶음 + 마운트', 220000, 1, '자율 이동과 장애물 인식'))
    if has('트랙', '궤도', 'track'):
        items.append(('주행 보강부', '소형 무한궤도 트랙 키트 또는 고무 트랙 벨트 세트', 180000, 2, '접지 면적을 늘려 험지 주행 안정성 향상'))
    return items


# =============================
# 물리 계산 및 기어비 분석
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
    part = get_parts(req_power, scale)

    req_tq = req_force * part['wheel_r'] / wheels
    req_rpm = speed_mps / (2 * math.pi * part['wheel_r']) * 60 if part['wheel_r'] > 0 else 1
    ideal = part['motor_rpm'] / max(req_rpm, 1)
    motor_nm = max(part['motor_nm'], req_tq / (max(ideal, 1) * eff) * 1.45)

    center = max(2, round(ideal))
    ratios = []
    for d in range(-2, 4):
        r = max(1, center + d)
        if r not in ratios:
            ratios.append(r)
    for r in [3, 4, 5, 6, 8, 10, 12, 15]:
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
        if typ == '균형형':
            reason = '목표 속도와 요구 토크의 균형이 가장 좋아 초기 후보로 적합'
        elif typ == '속도형':
            reason = '휠 RPM이 높아 빠른 주행에 유리하지만 토크 여유는 줄어듦'
        else:
            reason = '감속비가 커서 등판·하중에 유리하지만 최고속도는 낮아짐'
        rows.append(dict(ratio=r, rpm=rpm, tq=tq, margin=margin, speed_err=speed_err, score=score, typ=typ, reason=reason, driven=20 * r))

    rows = sorted(rows, key=lambda x: x['score'], reverse=True)[:5]
    for i, row in enumerate(rows):
        row['stars'] = 5 - i
    return part, rows, dict(speed_mps=speed_mps, grade=grade, req_power=req_power, req_tq=req_tq, req_rpm=req_rpm, motor_nm=motor_nm, req_force=req_force)


# =============================
# 스케치 생성: 한글 깨짐 방지 위해 그림 내부는 영문 라벨만 사용
# =============================
def draw_sketch(data, part, best):
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    ax.set_xlim(0, 1200)
    ax.set_ylim(720, 0)
    ax.axis('off')
    ax.set_facecolor('white')

    red = '#c8322b'
    blue = '#174a8b'
    purple = '#6f42c1'
    gray = '#666666'
    lw = 3.2

    purpose = data['purpose'].lower()
    extra = data['extra'].lower()

    is_scooter = '킥보드' in data['purpose'] or 'scooter' in purpose
    is_car = '전기차' in data['purpose'] or '차형' in data['purpose'] or '자동차' in data['purpose']
    is_track = any(k in extra for k in ['track']) or '궤도' in data['extra'] or '트랙' in data['extra']
    is_clean = '청소' in data['purpose'] or '브러시' in data['extra']
    is_service = '서비스' in data['purpose'] or '안내' in data['purpose']

    def rounded_box(x, y, w, h, color, lw_=3, fill=False, radius=24):
        ax.add_patch(patches.FancyBboxPatch((x, y), w, h,
                                            boxstyle=f'round,pad=0.02,rounding_size={radius}',
                                            linewidth=lw_, edgecolor=color,
                                            facecolor='none' if not fill else '#f7f7f7'))

    def wheel(x, y, r):
        ax.add_patch(patches.Circle((x, y), r, fill=False, edgecolor=red, lw=lw))
        ax.add_patch(patches.Circle((x, y), r * 0.42, fill=False, edgecolor=red, lw=2.2))
        ax.plot([x-r*0.65, x+r*0.65], [y, y], color=red, lw=1.6)
        ax.plot([x, x], [y-r*0.65, y+r*0.65], color=red, lw=1.6)

    def label(text, xy, xytext, color=blue):
        # 그림과 글씨가 겹치지 않도록 모든 라벨은 외곽에 배치
        ax.annotate(text, xy=xy, xytext=xytext,
                    arrowprops=dict(arrowstyle='->', color=color, lw=2.0, shrinkA=2, shrinkB=2),
                    color=color, fontsize=10.5, fontweight='bold', ha='center', va='center')

    # 제목: 영문만 사용해 한글 폰트 깨짐 방지
    ax.text(45, 55, 'Initial Layout Sketch', fontsize=17, fontweight='bold', color='#222222')
    ax.text(45, 82, 'simple mechanism placement memo', fontsize=11, color=gray)

    # 모빌리티 외형별 기본 뼈대
    if is_scooter:
        # 킥보드형: 데크 + 핸들 + 2륜
        ax.plot([250, 800], [455, 455], color=red, lw=lw)
        ax.plot([710, 760], [455, 270], color=red, lw=lw)
        ax.plot([730, 835], [270, 270], color=red, lw=lw)
        wheel(260, 510, 48)
        wheel(790, 510, 48)
        rounded_box(380, 410, 170, 45, blue, 3, radius=10)
        label('Battery / Controller', (465, 432), (465, 635), blue)
        rounded_box(210, 392, 110, 40, blue, 3, radius=8)
        label('Drive Motor', (250, 410), (125, 610), blue)
        ax.text(835, 260, 'Handle', color=purple, fontsize=10, fontweight='bold')

    elif is_car:
        # 자동차/EV형: 낮고 긴 차체 + 4륜 구조
        ax.plot([210, 830, 925, 120, 210], [355, 355, 490, 490, 355], color=red, lw=lw)
        ax.plot([310, 750, 820, 250, 310], [230, 230, 355, 355, 230], color=red, lw=lw)
        ax.plot([355, 705], [248, 340], color=red, lw=2.4)
        ax.plot([705, 355], [248, 340], color=red, lw=2.4)
        wheel(250, 535, 55)
        wheel(790, 535, 55)
        rounded_box(210, 415, 115, 42, blue, 3, radius=8)
        rounded_box(460, 400, 170, 52, blue, 3, radius=8)
        label('Drive Motor + Gearbox', (260, 435), (125, 630), blue)
        label('Battery / Inverter', (545, 425), (545, 655), blue)

    elif is_service:
        # 서비스로봇형: 수직 타워 + 하부 주행베이스
        rounded_box(260, 300, 540, 140, red, lw, radius=35)
        rounded_box(425, 120, 210, 180, red, lw, radius=45)
        wheel(330, 500, 48)
        wheel(730, 500, 48)
        rounded_box(300, 368, 110, 42, blue, 3, radius=8)
        rounded_box(500, 360, 160, 50, blue, 3, radius=8)
        label('Drive Motor', (350, 390), (130, 615), blue)
        label('Battery / Controller', (580, 385), (580, 640), blue)
        rounded_box(470, 145, 120, 45, purple, 3, radius=14)
        label('Sensor / Display', (530, 165), (900, 170), purple)

    elif is_track:
        # 궤도형: 트랙 벨트와 낮은 차체
        rounded_box(160, 455, 760, 135, red, lw, radius=68)
        wheel(275, 522, 45)
        wheel(510, 535, 38)
        wheel(755, 522, 45)
        rounded_box(240, 340, 610, 130, red, lw, radius=28)
        rounded_box(260, 380, 120, 45, blue, 3, radius=8)
        rounded_box(515, 370, 165, 52, blue, 3, radius=8)
        label('Track Drive Motor', (315, 400), (125, 650), blue)
        label('Battery / Controller', (595, 395), (610, 665), blue)
        label('Track Belt', (790, 545), (960, 630), purple)

    else:
        # 일반 대회/로봇형: 둥근 직사각 차체 + 상부 기구 배치
        rounded_box(190, 320, 690, 170, red, lw, radius=35)
        ax.plot([260, 370, 725, 810], [320, 210, 210, 320], color=red, lw=lw)
        ax.plot([375, 720], [230, 300], color=red, lw=2.4)
        ax.plot([720, 375], [230, 300], color=red, lw=2.4)
        wheel(280, 540, 55)
        wheel(800, 540, 55)
        if data['wheels'] >= 6:
            wheel(540, 552, 43)
        rounded_box(230, 375, 135, 47, blue, 3, radius=8)
        rounded_box(480, 360, 170, 55, blue, 3, radius=8)
        label('Drive Motor + Gearbox', (295, 398), (120, 640), blue)
        label('Battery / Controller', (565, 388), (565, 668), blue)

    # 공통 기어비 라벨
    gear_label = f'{best["ratio"]}:1 Gear'
    ax.text(395, 446, gear_label, fontsize=10.5, color=red, fontweight='bold')

    # 보조 장치 배치: 외곽 라벨, 본체와 중첩 최소화
    if 'intake' in extra or '인테이크' in data['extra']:
        rounded_box(900, 380, 120, 70, purple, 3, radius=10)
        label('Intake Motor', (960, 415), (1015, 315), purple)
    if 'feeder' in extra or '피더' in data['extra']:
        rounded_box(375, 270, 130, 55, purple, 3, radius=10)
        label('Feeder Motor', (440, 298), (165, 260), purple)
    if 'shooter' in extra or '슈터' in data['extra']:
        rounded_box(650, 125, 150, 80, purple, 3, radius=10)
        label('Shooter Motors', (725, 162), (930, 120), purple)
    if 'waterwheel' in extra or '워터휠' in data['extra'] or 'index' in extra:
        ax.add_patch(patches.Circle((665, 300), 38, fill=False, edgecolor=purple, lw=3))
        label('Index Wheel', (705, 300), (970, 260), purple)
    if 'lift' in extra or '리프트' in data['extra']:
        rounded_box(120, 210, 70, 210, purple, 3, radius=14)
        label('Lift Motor', (155, 275), (120, 135), purple)
    if '카메라' in data['extra'] or 'camera' in extra or 'lidar' in extra or '라이다' in data['extra'] or '센서' in data['extra']:
        rounded_box(515, 95, 90, 55, purple, 3, radius=14)
        label('Sensor', (560, 120), (750, 70), purple)
    if '브러시' in data['extra'] or 'brush' in extra or is_clean:
        ax.add_patch(patches.Rectangle((420, 535), 180, 28, fill=False, edgecolor=purple, lw=3))
        label('Brush Motor', (510, 550), (375, 655), purple)
    if '펌프' in data['extra'] or 'pump' in extra or '방제' in data['purpose']:
        rounded_box(710, 280, 95, 60, purple, 3, radius=10)
        label('Pump', (755, 308), (995, 205), purple)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# =============================
# Fusion 360 기어 도면
# =============================
def draw_gear_guide(best_ratio, mass):
    fig, ax = plt.subplots(figsize=(6.4, 3.7))
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_facecolor('white')

    module_val = 1.0 if mass <= 80 else 2.0
    drive_teeth = 20
    driven_teeth = int(20 * best_ratio)
    r_drive = drive_teeth * module_val / 2
    r_driven = driven_teeth * module_val / 2
    center_dist = r_drive + r_driven

    ax.add_patch(patches.Circle((0, 0), r_drive, fill=False, edgecolor='#174a8b', linewidth=2.4, linestyle='--'))
    ax.add_patch(patches.Circle((center_dist, 0), r_driven, fill=False, edgecolor='#c8322b', linewidth=2.4, linestyle='--'))
    ax.plot([0, center_dist], [0, 0], color='#444444', lw=1.4, linestyle='-.')
    ax.plot(0, 0, 'o', color='black', markersize=4)
    ax.plot(center_dist, 0, 'o', color='black', markersize=4)
    ax.text(0, -r_drive - 6, 'Motor gear\n20T', ha='center', fontsize=9, color='#174a8b')
    ax.text(center_dist, -r_driven - 6, f'Wheel gear\n{driven_teeth}T', ha='center', fontsize=9, color='#c8322b')
    ax.text(center_dist / 2, 8, f'Center distance: {center_dist:.1f} mm', ha='center', fontsize=9, color='#222222')
    ax.set_xlim(-r_drive - 20, center_dist + r_driven + 20)
    ax.set_ylim(-max(r_drive, r_driven) - 28, max(r_drive, r_driven) + 20)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    return module_val, center_dist


# =============================
# 설명문 생성
# =============================
def process_text(data, part, rows):
    best = rows[0]
    extra = data['extra'].lower()
    blocks = []
    blocks.append(
        f"이 스케치는 완성 외형도가 아니라, 제작자가 Fusion 360에서 첫 배치를 잡기 위한 초기 배치도입니다. "
        f"중앙 프레임은 배터리와 제어기를 싣는 기준 구조물이며, 하부의 주행 모터와 감속기는 {best['ratio']}:1 감속비를 통해 바퀴 토크를 확보합니다."
    )
    blocks.append(
        f"구동 과정은 제어기에서 모터 드라이버로 속도 명령을 보내고, 주행 모터가 감속기를 거쳐 바퀴축을 회전시키는 순서로 이루어집니다. "
        f"감속비가 커질수록 속도는 낮아지지만 바퀴 토크가 커져 경사나 하중에 대응하기 쉬워집니다."
    )
    if 'intake' in extra or '인테이크' in data['extra']:
        blocks.append("인테이크는 전면 또는 측면 하단에 배치하여 공이나 물체를 먼저 끌어들이는 역할을 합니다. 이 장치는 주행부와 동시에 동작할 수 있으므로 별도 모터와 롤러, 벨트 장력이 필요합니다.")
    if 'feeder' in extra or '피더' in data['extra']:
        blocks.append("피더는 인테이크로 들어온 물체를 저장부나 슈터 쪽으로 일정하게 보내는 중간 이송 장치입니다. 속도가 너무 빠르면 걸림이 생길 수 있어 주행 모터와 별도의 저속 제어가 유리합니다.")
    if 'shooter' in extra or '슈터' in data['extra']:
        blocks.append("슈터는 고속 회전 플라이휠로 물체를 발사하는 장치입니다. 주행 구동부보다 높은 RPM 안정성이 중요하므로 별도의 고속 DC/BLDC 모터와 견고한 브라켓이 필요합니다.")
    if 'waterwheel' in extra or '워터휠' in data['extra'] or 'index' in extra:
        blocks.append("워터휠 또는 인덱스 휠은 물체의 방향과 공급 순서를 맞추는 역할을 합니다. 인테이크-피더-슈터가 연속 동작할 때 물체가 한 번에 몰리지 않도록 흐름을 조절합니다.")
    if '트랙' in data['extra'] or '궤도' in data['extra'] or 'track' in extra:
        blocks.append("무한궤도는 접지 면적을 넓혀 험지에서 미끄러짐을 줄입니다. 대신 마찰과 회전 저항이 커지므로 모터 토크와 배터리 용량에 더 큰 여유를 두는 것이 좋습니다.")
    if data['scale'] == 'student':
        blocks.append("학생용 제작에서는 금속 프레임을 먼저 주문하기보다 Fusion 360으로 차체, 모터마운트, 기어커버, 베어링 하우징을 설계한 뒤 PLA/PETG/ABS로 출력해 조립하는 방식을 우선 권장합니다. 수정이 쉽고 비용을 낮출 수 있기 때문입니다.")
    return "\n\n".join(blocks)


def build_report(data, part, rows, calc, budget, total):
    lines = []
    lines.append("모빌리티 구동계 초기 설계 도움 시스템 결과 요약")
    lines.append(f"용도: {data['purpose']}")
    lines.append(f"스케일: {SCALE_LABEL.get(data['scale'], data['scale'])}")
    lines.append(f"질량: {data['mass']} kg")
    lines.append(f"목표 속도: {data['speed']} {'km/h' if data['unit']=='kmh' else 'm/s'}")
    lines.append(f"운행 환경: {ENV_LABEL.get(data['env'], data['env'])}")
    lines.append(f"기타 요구사항: {data['extra']}")
    lines.append("")
    lines.append(f"요구 동력: {calc['req_power']:.0f} W")
    lines.append(f"바퀴당 요구 토크: {calc['req_tq']:.2f} Nm")
    lines.append(f"필요 휠 RPM: {calc['req_rpm']:.1f} RPM")
    lines.append(f"추천 모터: {part['motor']}")
    lines.append("")
    lines.append("기어비 후보:")
    for i, r in enumerate(rows, 1):
        lines.append(f"{i}위 {stars(r['stars'])}: {r['ratio']}:1, 20T:{r['driven']}T, {r['typ']} - {r['reason']}")
    lines.append("")
    lines.append("예산안:")
    for item in budget:
        cat, name, unit, qty, *_ = item
        lines.append(f"- {cat}: {name} / {unit:,}원 x {qty} = {unit*qty:,}원")
    lines.append(f"총 예상 제작 비용: 약 {total:,}원")
    return "\n".join(lines)


# =============================
# UI
# =============================
st.title("⚙️ 모빌리티 구동계 초기 설계 도움 시스템")
st.caption("사용자의 목적과 운행 조건을 바탕으로 구동계, 기어비, 부품, 예산, 초기 배치 스케치를 제안하는 보조 도구입니다.")

left, right = st.columns([1.05, 1.0])

with left:
    st.subheader("빠른 설정")
    option_list = ["직접 입력"] + [f"{k}. {v['purpose']} ({v['mass']}kg)" for k, v in PRESETS.items()]
    selected_option = st.selectbox("프리셋 선택", option_list, index=0)

with right:
    st.subheader("직접 상세 조건 입력")
    st.caption("직접 입력을 사용할 때는 아래 칸을 비워둬도 내부 기본값으로 계산됩니다.")

if selected_option != "직접 입력":
    preset_key = int(selected_option.split(".")[0])
    data = PRESETS[preset_key].copy()
    st.info(f"선택된 프리셋: {data['purpose']}")
else:
    c1, c2, c3 = st.columns(3)
    with c1:
        scale_label = st.selectbox('스케일/용도', ['', 'student', 'research', 'industry'], format_func=lambda x: '선택 안 함' if x == '' else SCALE_LABEL.get(x, x), index=0)
        purpose_in = st.text_input('목표 모빌리티의 용도', placeholder='예: 공 수집 및 발사 로봇')
        mass_in = st.text_input('예상 질량 (kg)', placeholder='예: 35')
    with c2:
        speed_in = st.text_input('목표 속도', placeholder='예: 1.5')
        unit_in = st.selectbox('속도 단위', ['', 'mps', 'kmh'], format_func=lambda x: '선택 안 함' if x == '' else ('m/s' if x == 'mps' else 'km/h'), index=0)
        wheels_in = st.text_input('구동 바퀴 수', placeholder='예: 4')
    with c3:
        env_in = st.selectbox('운행 환경', ['', 'normal', 'indoor', 'obstacle', 'extreme'], format_func=lambda x: '선택 안 함' if x == '' else ENV_LABEL.get(x, x), index=0)
        extra_in = st.text_area('기타 요구사항 (상세할수록 구체화)', placeholder='예: intake, feeder, shooter, 카메라, 방수, 궤도 등', height=115)

    data = dict(
        scale=scale_label or 'student',
        purpose=purpose_in.strip() or '학생용 이동 로봇',
        mass=safe_float(mass_in, 35.0),
        speed=safe_float(speed_in, 1.5),
        unit=unit_in or 'mps',
        wheels=safe_int(wheels_in, 4),
        env=env_in or 'indoor',
        extra=extra_in.strip() or '없음'
    )

part, rows, calc = analyze(data)

st.divider()

# 결과 1
st.subheader("1. 물리 모델 역산 결과")
col1, col2, col3, col4 = st.columns(4)
col1.metric("요구 동력", f"{calc['req_power']:.0f} W")
col2.metric("바퀴당 요구 토크", f"{calc['req_tq']:.2f} Nm")
col3.metric("필요 휠 RPM", f"{calc['req_rpm']:.1f} RPM")
col4.metric("적용 경사각", f"{calc['grade']}°")

st.info(f"**추천 주행 모터:** {part['motor']}  \n\n**역산 기준 토크:** {calc['motor_nm']:.2f} Nm")

with st.expander("모터 선택 스펙트럼 보기", expanded=True):
    st.write("입력 조건과 요구 동력에 따라 아래 후보군 중에서 제작 난도, 예산, 제어 방식에 맞춰 선택할 수 있습니다.")
    st.table([{"후보": m} for m in part.get('motor_options', [])])

with st.expander("기어/감속기 선택 스펙트럼 보기", expanded=False):
    st.table([{"후보": g} for g in part.get('gear_options', [])])

# 결과 2
st.subheader("2. 기어비 후보 분석")
st.table([
    {
        "순위": f"{i}위",
        "추천도": stars(r['stars']),
        "기어비": f"{r['ratio']}:1",
        "기어 잇수": f"20T : {r['driven']}T",
        "예상 휠 RPM": f"{r['rpm']:.1f}",
        "예상 휠 토크": f"{r['tq']:.2f} Nm",
        "유형": r['typ'],
        "추천 이유": r['reason']
    } for i, r in enumerate(rows, 1)
])

st.caption("표 해석: 추천도가 높을수록 목표 속도와 요구 토크의 균형이 좋습니다. 단, 험지·고하중이 목적이면 별점이 조금 낮더라도 토크형 후보가 더 적합할 수 있습니다.")

# 결과 3 예산
st.subheader("3. 정밀 예산안")
budget = [
    ('주행 구동부', part['motor'], part['motor_cost'], data['wheels'], '바퀴축을 직접 구동하는 핵심 모터'),
    ('주행 구동부', part['gear'], part['gear_cost'], data['wheels'], '모터 회전수를 감속하고 바퀴 토크를 증폭'),
    ('바퀴/축/베어링', part['wheel'], part['wheel_cost'], data['wheels'], '하중 지지와 실제 노면 접촉'),
    ('제어/전원부', part['control'], part['control_cost'], 1, '배터리, 드라이버, 제어보드, 보호회로'),
    ('주요 구성 형체', part['frame'], part['frame_cost'], 1, part.get('frame_basis', '프레임 및 체결류'))
] + aux_items(data['extra'])

total = sum(x[2] * x[3] for x in budget)
st.table([
    {"분류": cat, "상세 품명 및 규격": name, "단가": f"{unit:,}원", "수량": qty, "소계": f"{unit*qty:,}원", "역할": role if role else ''}
    for cat, name, unit, qty, *role in budget
])
st.success(f"총 예상 제작 비용: 약 {total:,}원")
st.caption("주의: 위 금액은 초기 설계 규모 산정을 위한 추정 예산입니다. 실제 비용은 구매처, 배송비, 수량 할인, 가공 의뢰비, 출력 실패율에 따라 달라질 수 있습니다.")

# 결과 4 Fusion 360
st.subheader("4. Fusion 360 기어 도면 & 초기 설계 가이드")
g1, g2 = st.columns([1, 1])
with g1:
    if rows:
        module_val, center_dist = draw_gear_guide(rows[0]['ratio'], data['mass'])
with g2:
    if rows:
        st.markdown("""
**초기 스케치 가이드**

1. **중심 거리**: 기어 모듈 기준으로 두 축 사이의 거리를 먼저 잡습니다.  
2. **조인트 설정**: Fusion 360에서 모터축과 바퀴축에 각각 `Revolute` 조인트를 적용합니다.  
3. **Motion Link**: 모터축 360° 회전 시 바퀴축이 `360 / 감속비` 만큼 회전하도록 설정합니다.  
4. **3D 프린팅 공차**: 학생용 3D 프린팅 부품은 축 구멍과 베어링 홀을 도면보다 약 `+0.2mm` 크게 잡는 것이 조립에 유리합니다.  
5. **학생용 제작 권장**: 차체, 모터마운트, 기어커버, 배터리 트레이는 Fusion 360으로 먼저 설계한 뒤 PLA/PETG로 출력해 반복 수정하는 방식을 권장합니다.
""")
        st.write(f"- 추천 감속비: **{rows[0]['ratio']}:1**")
        st.write(f"- Motion Link 예시: **360° : {360/rows[0]['ratio']:.1f}°**")

# 결과 5 스케치
st.subheader("5. 초기 배치 스케치")
st.caption("그림 내부 라벨은 Streamlit Cloud 한글 폰트 깨짐을 피하기 위해 영문으로 표시됩니다. 아래 설명에서 한국어 의미를 함께 확인할 수 있습니다.")
if rows:
    draw_sketch(data, part, rows[0])

st.markdown("### 구조물과 장치의 유기적 역할 및 구현 프로세스")
st.write(process_text(data, part, rows))

with st.expander("그림 라벨 한국어 설명", expanded=True):
    st.markdown("""
- **Drive Motor / Drive Motor + Gearbox**: 주행 모터 및 감속기
- **Battery / Controller**: 배터리, 모터 드라이버, 제어보드
- **Intake Motor**: 물체를 끌어들이는 인테이크 구동부
- **Feeder Motor**: 수집된 물체를 다음 장치로 보내는 이송부
- **Shooter Motors**: 공이나 물체를 발사하는 고속 플라이휠 모터
- **Index Wheel**: 물체 공급 순서를 제어하는 워터휠/인덱스 휠
- **Track Belt**: 험지 주행용 무한궤도 벨트
- **Sensor**: 카메라, 라이다 등 인식 장치
""")

# 복사용 보고서
st.subheader("6. 테스트베드/보고서용 전체 내용 복사")
report = build_report(data, part, rows, calc, budget, total)
st.code(report, language="text")
st.caption("위 텍스트 박스 오른쪽 상단의 복사 아이콘을 눌러 보고서나 테스트베드 문서에 붙여넣을 수 있습니다.")

