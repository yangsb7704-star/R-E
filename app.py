import math
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# =========================================================
# 페이지 설정
# =========================================================
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
    'indoor': '실내·자율 이동/완만한 경사',
    'obstacle': '장애물 많은 지형/요철·문턱',
    'extreme': '험한 지형/급경사·비포장'
}

UNIT_LABELS = {
    'mps': 'm/s',
    'kmh': 'km/h'
}

# =========================================================
# 유틸 함수
# =========================================================
def env_grade(env):
    return {'normal': 2, 'indoor': 8, 'obstacle': 15, 'extreme': 35}.get(env, 8)


def parse_float(text, default):
    try:
        if text is None or str(text).strip() == '':
            return default
        return float(str(text).strip())
    except ValueError:
        return default


def parse_int(text, default):
    try:
        if text is None or str(text).strip() == '':
            return default
        return int(float(str(text).strip()))
    except ValueError:
        return default


def stars(n):
    n = max(1, min(5, int(n)))
    return '★' * n + '☆' * (5 - n)


def classify_parts(req_power, scale):
    """요구 동력과 제작 스케일에 따른 주요 부품 추천 DB."""
    if req_power <= 60 and scale != 'industry':
        return dict(
            tier='소형', wheel_r=0.05, motor_rpm=4000, motor_nm=0.10,
            motor_name='Parvalux PBL42 Range BLDC 모터',
            motor_spec='24~48V, 4000rpm, 26~42W급, 연속토크 약 0.06~0.10Nm',
            motor_cost=85000,
            gear_name='미스미 소모듈 평기어 M0.8~1.0',
            gear_spec='압력각 20°, C3604 황동 또는 POM, 소형 로봇 감속용',
            gear_cost=18000,
            wheel_name='100mm 우레탄/고무 로봇 바퀴 세트',
            wheel_spec='Ø6mm SUS304 축, 소형 베어링 포함 가정',
            wheel_cost=18000,
            control_name='Arduino/ESP32 제어보드 + 소형 DC/BLDC 드라이버',
            control_spec='12~24V 배터리, 소형 퓨즈, 기본 배선 포함',
            control_cost=120000,
            frame_name='PLA/PETG 3D 프린팅 브라켓 + 소형 알루미늄 프로파일',
            frame_spec='학생용 프로토타입 차체, 모터 마운트, 간단한 상판 포함',
            frame_cost=90000
        )
    if req_power <= 220 and scale != 'industry':
        return dict(
            tier='중소형', wheel_r=0.10, motor_rpm=3000, motor_nm=0.50,
            motor_name='Parvalux PBL60 Range BLDC 모터',
            motor_spec='24~48V, 3000rpm, 104~157W급, 연속토크 약 0.33~0.50Nm',
            motor_cost=240000,
            gear_name='PGx42/GB28급 기어헤드 또는 미스미 M2.0 S45C 평기어',
            gear_spec='중소형 구동축 감속용, 축 정렬 브라켓 필요',
            gear_cost=65000,
            wheel_name='200mm 솔리드 우레탄 바퀴 세트',
            wheel_spec='Ø10mm S45C 축, 플랜지 베어링 포함 가정',
            wheel_cost=55000,
            control_name='24V BLDC 드라이버 2~4ch + 24V 리튬 배터리',
            control_spec='10~20Ah 배터리, 퓨즈, 스위치, 기본 배선 포함',
            control_cost=420000,
            frame_name='2020/3030 알루미늄 프로파일 프레임 + 3D프린팅 모터마운트',
            frame_spec='대회/탐구용 섀시, 장치 고정 브라켓 포함',
            frame_cost=180000
        )
    if req_power <= 650 or scale == 'research':
        return dict(
            tier='중형', wheel_r=0.12, motor_rpm=4000, motor_nm=1.40,
            motor_name='Parvalux PBL86 Range BLDC 모터',
            motor_spec='48V, 4000rpm, 419~586W급, 연속토크 약 1.00~1.40Nm',
            motor_cost=480000,
            gear_name='Parvalux PGx70/PGx52 기어박스 또는 미스미 경제형 평기어 M3.0',
            gear_spec='GB/T 10095 8등급 수준, 중형 구동 감속용',
            gear_cost=101396,
            wheel_name='250mm 고하중 우레탄 바퀴 세트',
            wheel_spec='Ø15mm S45C 열처리 축, 하우징 베어링 포함 가정',
            wheel_cost=95000,
            control_name='48V BLDC 드라이버 + 48V 20Ah 배터리팩',
            control_spec='BMS, 비상정지 스위치, 차단기, 기본 배선 포함',
            control_cost=900000,
            frame_name='3030/4040 알루미늄 프로파일 또는 절곡 알루미늄 판재 섀시',
            frame_spec='연구용 프로토타입 차체, 장치 장착용 보강 프레임 포함',
            frame_cost=350000
        )
    return dict(
        tier='대형', wheel_r=0.25, motor_rpm=3000, motor_nm=8.00,
        motor_name='AC 서보모터 SD13/SD48급 또는 산업용 BLDC 서보',
        motor_spec='1kW 이상급, 인버터/서보드라이브 제어, 고하중 주행용',
        motor_cost=1200000,
        gear_name='헬리컬/웜 감속기 또는 LIW/MWS급 고토크 기어헤드',
        gear_spec='28~45Nm급 이상, 열처리 기어, 산업용 감속 모듈 가정',
        gear_cost=850000,
        wheel_name='13인치 이상 튜브/솔리드 타이어 구동 세트',
        wheel_spec='Ø20mm 이상 구동축, 자동차형 베어링 또는 허브 포함 가정',
        wheel_cost=220000,
        control_name='서보 드라이브/인버터 + 48V~고전압 배터리팩',
        control_spec='BMS, 차단기, 비상정지, 고전류 배선 포함',
        control_cost=3500000,
        frame_name='강철 사각파이프 용접 프레임 또는 주문제작 절곡 섀시',
        frame_spec='산업용 하중 대응 차체, 모터/감속기 브라켓 제작 포함',
        frame_cost=2200000
    )


def aux_items(extra):
    e = extra.lower()
    items = []

    def has(*ks):
        return any(k.lower() in e or k in extra for k in ks)

    if has('intake', '인테이크'):
        items.append(('보조 기구부', 'Intake 흡입 롤러용 775/550급 DC 모터 또는 소형 BLDC', '고무 롤러, 벨트, 브라켓 포함', 95000, 1, '바닥의 공/물체를 로봇 내부로 끌어올림'))
    if has('feeder', '피더'):
        items.append(('보조 기구부', 'Feeder 이송용 서보모터/기어드 DC 모터', '타이밍벨트 풀리, 가이드 레일 포함', 80000, 1, '수집된 물체를 슈터나 저장부로 일정하게 공급'))
    if has('shooter', '슈터'):
        items.append(('보조 기구부', 'Shooter 고속 플라이휠용 BLDC/DC 모터 2개', '플라이휠, 모터 브라켓, 벨트 포함', 140000, 2, '고속 회전 휠로 공을 목표 방향으로 발사'))
    if has('waterwheel', '워터휠'):
        items.append(('보조 기구부', 'Waterwheel/색인 휠용 AC/BLDC 보조모터', '원판형 휠, 허브, 지지 브라켓 포함', 120000, 1, '공 또는 물체의 방향과 공급 순서를 제어'))
    if has('lift', '리프트', '엘리베이터'):
        items.append(('보조 기구부', 'Lift 승강용 웜기어드 모터', '리니어 가이드, 랙기어, 상하 브라켓 포함', 160000, 1, '상하 이동 또는 높이 조절 기능 수행'))
    if has('lidar', '라이다', '카메라', '센서'):
        items.append(('센서/인식부', '2D LiDAR/카메라/초음파 센서 묶음', '센서 마운트, 케이블, 보호 커버 포함', 220000, 1, '자율 이동과 장애물 인식'))
    if has('트랙', '궤도', 'track'):
        items.append(('주행 보강부', '소형 무한궤도 트랙 키트 또는 고무 트랙 벨트 세트', '스프로킷, 아이들러, 장력 조절부 포함', 180000, 2, '접지 면적을 늘려 험지 주행 안정성 향상'))
    if has('방수', '방진', 'ip'):
        items.append(('보호/내구부', '방수방진 전장 박스 및 케이블 글랜드', 'IP 등급 박스, 실링재, 방수 커넥터 포함', 90000, 1, '비, 먼지, 흙으로부터 제어부 보호'))
    return items


def analyze(data):
    scale, mass, speed, unit = data['scale'], data['mass'], data['speed'], data['unit']
    wheels, env, extra = data['wheels'], data['env'], data['extra']

    speed_mps = speed / 3.6 if unit == 'kmh' else speed
    grade = env_grade(env)
    g, crr, sf, eff = 9.81, 0.02, 1.5, 0.85

    base_res = crr * mass * g * math.cos(math.radians(grade)) + mass * g * math.sin(math.radians(grade))
    req_force = base_res * sf
    req_power = base_res * speed_mps * sf
    part = classify_parts(req_power, scale)

    req_tq = req_force * part['wheel_r'] / max(wheels, 1)
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

        if r < center:
            typ = '속도형'
            reason = '감속비가 낮아 휠 RPM이 높습니다. 빠른 주행이 필요한 경우 유리하지만 토크 여유는 줄어듭니다.'
        elif r == center:
            typ = '균형형'
            reason = '목표 속도와 요구 토크의 균형이 가장 좋아 초기 설계 기준안으로 적합합니다.'
        else:
            typ = '토크형'
            reason = '감속비가 커서 등판, 하중 운반, 험지 돌파에 유리하지만 최고속도는 낮아집니다.'

        rows.append(dict(
            ratio=r, rpm=rpm, tq=tq, margin=margin, speed_err=speed_err,
            score=score, typ=typ, reason=reason, driven=20 * r
        ))

    rows = sorted(rows, key=lambda x: x['score'], reverse=True)[:5]
    for i, row in enumerate(rows):
        row['stars'] = 5 - i

    calc = dict(
        speed_mps=speed_mps,
        speed_kmh=speed_mps * 3.6,
        grade=grade,
        req_power=req_power,
        req_force=req_force,
        req_tq=req_tq,
        req_rpm=req_rpm,
        motor_nm=motor_nm,
        ideal_ratio=ideal
    )
    return part, rows, calc

# =========================================================
# 스케치 및 가이드
# =========================================================
def draw_sketch(data, part, best):
    """초기 아이디어 스케치. 모빌리티 유형에 따라 뼈대를 다르게 그림."""
    try:
        fig, ax = plt.subplots(figsize=(11, 6))
        ax.set_xlim(0, 1100)
        ax.set_ylim(700, 0)
        ax.axis('off')
        ax.set_facecolor('white')

        red, blue, gray = '#d42323', '#174a8b', '#555555'
        lw = 3.2
        purpose = data['purpose'].lower()
        extra = data['extra']
        e = extra.lower()

        is_scooter = any(k in purpose for k in ['킥보드', '스쿠터'])
        is_car = any(k in purpose for k in ['전기차', '자동차', '차형'])
        is_track = ('track' in e) or ('궤도' in extra) or ('트랙' in extra)
        is_competition = any(k in e for k in ['intake', 'feeder', 'shooter', 'waterwheel']) or any(k in extra for k in ['인테이크', '피더', '슈터', '워터휠'])

        def label(text, xy, xytext):
            ax.annotate(text, xy=xy, xytext=xytext,
                        arrowprops=dict(arrowstyle='->', color=blue, lw=2.0),
                        color=blue, fontsize=11, fontweight='bold')

        def wheel(x, y, r):
            ax.add_patch(patches.Circle((x, y), r, fill=False, edgecolor=red, lw=lw))
            ax.add_patch(patches.Circle((x, y), r * 0.45, fill=False, edgecolor=red, lw=2.0))
            ax.plot([x-r*0.6, x+r*0.6], [y, y], color=red, lw=1.7)
            ax.plot([x, x], [y-r*0.6, y+r*0.6], color=red, lw=1.7)

        # 기본 바닥선
        ax.plot([90, 980], [610, 610], color=gray, lw=1.5, alpha=0.6)

        if is_scooter:
            # 킥보드형 뼈대
            wheel(270, 560, 45)
            wheel(760, 560, 45)
            ax.plot([270, 760], [515, 515], color=red, lw=lw)
            ax.plot([690, 760], [515, 320], color=red, lw=lw)
            ax.plot([735, 810], [320, 320], color=red, lw=lw)
            ax.plot([330, 640], [500, 430], color=red, lw=lw)
            ax.add_patch(patches.Rectangle((250, 465), 120, 40, fill=False, edgecolor=blue, lw=2.6))
            ax.add_patch(patches.Rectangle((500, 470), 140, 38, fill=False, edgecolor=blue, lw=2.6))
            label('허브/주행 모터', (270, 560), (90, 520))
            label('배터리팩', (560, 490), (455, 665))
            label('조향 핸들부', (780, 320), (825, 260))

        elif is_car:
            # 자동차형 뼈대
            wheel(270, 555, 55)
            wheel(770, 555, 55)
            ax.plot([210, 835, 880, 170, 210], [435, 435, 525, 525, 435], color=red, lw=lw)
            ax.plot([300, 690, 760, 245, 300], [315, 315, 435, 435, 315], color=red, lw=lw)
            ax.plot([360, 700], [315, 435], color=red, lw=lw)
            ax.add_patch(patches.Rectangle((220, 450), 120, 42, fill=False, edgecolor=blue, lw=2.6))
            ax.add_patch(patches.Rectangle((470, 450), 160, 48, fill=False, edgecolor=blue, lw=2.6))
            label('구동 모터/감속기', (280, 470), (70, 500))
            label('배터리/제어기', (545, 475), (460, 665))
            label('차체 프레임', (560, 330), (770, 300))

        else:
            # 일반 로봇/대회형/험지형 뼈대
            if is_track:
                ax.add_patch(patches.FancyBboxPatch((155, 505), 730, 100,
                                                    boxstyle='round,pad=0,rounding_size=50',
                                                    fill=False, edgecolor=red, lw=lw))
                wheel(260, 555, 42)
                wheel(780, 555, 42)
                wheel(520, 565, 35)
                label('무한궤도/트랙', (515, 600), (770, 640))
            else:
                wheel(250, 560, 52)
                wheel(790, 560, 52)
                if data['wheels'] >= 6:
                    wheel(520, 570, 42)

            # 프레임과 상부 구조
            ax.plot([230, 790, 850, 185, 230], [445, 445, 525, 525, 445], color=red, lw=lw)
            ax.plot([315, 720, 790, 250, 315], [285, 285, 445, 445, 285], color=red, lw=lw)
            ax.plot([360, 710], [295, 430], color=red, lw=lw)
            ax.plot([705, 365], [295, 430], color=red, lw=lw)

            # 주행 모터, 제어기
            ax.add_patch(patches.Rectangle((200, 455), 105, 42, fill=False, edgecolor=blue, lw=2.7))
            ax.add_patch(patches.Circle((335, 475), 24, fill=False, edgecolor=blue, lw=2.7))
            ax.add_patch(patches.Rectangle((430, 435), 155, 48, fill=False, edgecolor=blue, lw=2.7))
            label('주행 모터 + 감속기', (250, 475), (55, 640))
            label('배터리/제어기', (505, 480), (420, 670))

            # 대회형 장치 배열
            if 'intake' in e or '인테이크' in extra:
                ax.add_patch(patches.Rectangle((805, 430), 110, 65, fill=False, edgecolor=red, lw=2.8))
                ax.plot([820, 900], [462, 462], color=red, lw=2.2)
                label('intake 흡입부', (865, 462), (865, 610))
            if 'feeder' in e or '피더' in extra:
                ax.add_patch(patches.Rectangle((330, 330), 125, 58, fill=False, edgecolor=red, lw=2.8))
                ax.arrow(350, 360, 80, 0, head_width=12, head_length=16, fc=red, ec=red, lw=1.2)
                label('feeder 이송부', (340, 350), (45, 340))
            if 'shooter' in e or '슈터' in extra:
                ax.add_patch(patches.Rectangle((545, 170), 165, 88, fill=False, edgecolor=red, lw=2.8))
                ax.add_patch(patches.Circle((590, 214), 25, fill=False, edgecolor=red, lw=2.2))
                ax.add_patch(patches.Circle((660, 214), 25, fill=False, edgecolor=red, lw=2.2))
                label('shooter 발사 모터', (650, 190), (760, 130))
            if 'waterwheel' in e or '워터휠' in extra:
                ax.add_patch(patches.Circle((615, 360), 38, fill=False, edgecolor=red, lw=2.8))
                ax.plot([615, 615], [330, 390], color=red, lw=1.8)
                ax.plot([585, 645], [360, 360], color=red, lw=1.8)
                label('waterwheel 색인', (650, 360), (800, 365))
            if is_competition:
                ax.text(725, 475, '공 이동 경로', color=blue, fontsize=10, fontweight='bold')
                ax.arrow(820, 455, -170, -80, head_width=14, head_length=20, fc=blue, ec=blue, lw=1.3, alpha=0.75)

        ax.text(40, 55, '초기 아이디어 스케치', fontsize=17, fontweight='bold')
        ax.text(40, 88, data['purpose'][:46], fontsize=12)
        ax.text(40, 118, f"스케일: {SCALE_LABELS.get(data['scale'], data['scale'])} / 환경: {ENV_LABELS.get(data['env'], data['env'])}", fontsize=10, color=gray)
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.warning(f'스케치 표시 중 오류 발생: {e}')


def draw_fusion_gear_guide(best_ratio, mass):
    try:
        module = 1.0 if mass <= 80 else 2.0
        drive_teeth = 20
        driven_teeth = int(20 * best_ratio)
        r1 = drive_teeth * module / 2
        r2 = driven_teeth * module / 2
        center_dist = r1 + r2

        fig, ax = plt.subplots(figsize=(7, 3.8))
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_facecolor('white')
        ax.add_patch(patches.Circle((0, 0), r1, fill=False, edgecolor='#174a8b', lw=2.5, linestyle='--'))
        ax.add_patch(patches.Circle((center_dist, 0), r2, fill=False, edgecolor='#d42323', lw=2.5, linestyle='--'))
        ax.plot([0, center_dist], [0, 0], color='#555', lw=1.5, linestyle='-.')
        ax.plot(0, 0, 'ko')
        ax.plot(center_dist, 0, 'ko')
        ax.text(0, -r1-5, f'구동기어\n{drive_teeth}T', ha='center', fontsize=9)
        ax.text(center_dist, -r2-5, f'피동기어\n{driven_teeth}T', ha='center', fontsize=9)
        ax.text(center_dist/2, max(r1, r2)+8, f'중심거리 ≈ {center_dist:.1f} mm', ha='center', fontsize=11, fontweight='bold')
        ax.set_xlim(-r1-15, center_dist+r2+15)
        ax.set_ylim(-max(r1, r2)-25, max(r1, r2)+25)
        plt.tight_layout()
        return fig, module, center_dist, driven_teeth
    except Exception:
        return None, 1.0, 0, 20


def process_description(data, part, rows, calc):
    extra = data['extra']
    e = extra.lower()
    lines = []
    lines.append(f"이 모빌리티는 '{data['purpose']}' 용도에 맞춰 {ENV_LABELS.get(data['env'], data['env'])} 환경에서 움직이는 것을 기준으로 초기 구동계를 잡았습니다.")
    lines.append(f"주행 구동부는 {part['motor_name']}와 {part['gear_name']}를 통해 모터의 고속 회전을 바퀴에 필요한 토크로 바꾸며, 계산상 바퀴당 최소 {calc['req_tq']:.2f} Nm 이상의 출력 토크가 필요합니다.")
    lines.append("프레임/차체는 단순한 외피가 아니라 모터 마운트, 축 지지부, 배터리 고정부, 보조 장치의 기준면 역할을 하므로 초기 CAD 단계에서 가장 먼저 기준 스케치로 잡아야 합니다.")
    if 'intake' in e or '인테이크' in extra:
        lines.append("Intake는 전면 하단에 배치하여 물체를 먼저 받아들이고, 고무 롤러 또는 벨트로 내부 이송 경로에 올리는 역할을 합니다.")
    if 'feeder' in e or '피더' in extra:
        lines.append("Feeder는 intake가 받은 물체를 일정한 간격으로 shooter, 저장부 또는 waterwheel 쪽으로 넘겨 장치 간 동작이 끊기지 않도록 합니다.")
    if 'shooter' in e or '슈터' in extra:
        lines.append("Shooter는 상부나 후방에 배치하고, 고속 플라이휠 모터가 충분히 회전한 뒤 feeder가 물체를 밀어 넣는 순서로 작동시키는 것이 안정적입니다.")
    if 'waterwheel' in e or '워터휠' in extra:
        lines.append("Waterwheel은 물체의 방향과 순서를 정렬하는 색인 장치로, shooter나 feeder 앞단에 배치하면 연속 동작 제어가 쉬워집니다.")
    if '궤도' in extra or '트랙' in extra or 'track' in e:
        lines.append("궤도/트랙은 접지 면적을 늘려 험지에서 미끄러짐을 줄이는 대신 회전 저항과 제작 난도가 증가하므로 장력 조절 구조를 함께 설계해야 합니다.")
    lines.append("실행 프로세스는 ① 제어기 전원 인가 → ② 주행 모터 속도 제어 → ③ 센서/조종 입력 확인 → ④ 보조 장치 순차 구동 → ⑤ 과전류·전복·정지 조건 감시 순서로 구성하는 것이 적합합니다.")
    return "\n\n".join(lines)


def build_testbed_text(data, part, rows, calc, budget_rows, total):
    best = rows[0] if rows else None
    text = []
    text.append("[모빌리티 구동계 초기 설계 도움 시스템 결과 요약]")
    text.append(f"용도: {data['purpose']}")
    text.append(f"제작 스케일: {SCALE_LABELS.get(data['scale'], data['scale'])}")
    text.append(f"운행 환경: {ENV_LABELS.get(data['env'], data['env'])} / 적용 경사각: {calc['grade']}도")
    text.append(f"질량: {data['mass']} kg / 목표 속도: {calc['speed_mps']:.2f} m/s ({calc['speed_kmh']:.1f} km/h) / 구동 바퀴 수: {data['wheels']}개")
    text.append(f"요구 동력: {calc['req_power']:.0f} W / 바퀴당 요구 토크: {calc['req_tq']:.2f} Nm / 필요 휠 RPM: {calc['req_rpm']:.1f} RPM")
    text.append(f"추천 모터: {part['motor_name']} ({part['motor_spec']})")
    text.append(f"추천 기어: {part['gear_name']} ({part['gear_spec']})")
    if best:
        text.append(f"1순위 감속비: {best['ratio']}:1 / 기어 잇수: 20T:{best['driven']}T / 예상 휠 RPM: {best['rpm']:.1f} / 예상 토크: {best['tq']:.2f} Nm")
    text.append(f"총 예상 제작 비용: 약 {total:,}원")
    text.append("예산 항목:")
    for row in budget_rows:
        text.append(f"- {row['분류']}: {row['품목']} / 규격: {row['규격/근거']} / 단가 {row['단가']} × {row['수량']} = {row['합계']}")
    text.append("작동 프로세스:")
    text.append(process_description(data, part, rows, calc))
    return "\n".join(text)

# =========================================================
# Streamlit 화면
# =========================================================
st.title("⚙️ 모빌리티 구동계 초기 설계 도움 시스템")
st.caption("제작자가 탐구와 설계를 시작할 수 있도록 물리 계산 기반의 초기 후보안, 부품, 예산, CAD 가이드를 제공하는 보조 도구입니다.")

with st.sidebar:
    st.header("입력 방식")
    option_list = ["직접 입력"] + [f"{k}. {v['purpose']} ({v['mass']}kg)" for k, v in PRESETS.items()]
    selected_option = st.selectbox("빠른 설정 또는 직접 입력 선택", option_list, index=0)

    st.divider()

    if selected_option != "직접 입력":
        preset_key = int(selected_option.split(".")[0])
        data = PRESETS[preset_key].copy()
        st.success(f"프리셋 적용: {data['purpose']}")
        st.write(f"스케일: {SCALE_LABELS[data['scale']]}")
        st.write(f"환경: {ENV_LABELS[data['env']]}")
        st.write(f"속도: {data['speed']} {UNIT_LABELS[data['unit']]}")
    else:
        st.subheader("직접 상세 조건 입력")
        st.caption("입력란은 비워둘 수 있습니다. 비워두면 내부 기본값으로 계산합니다.")

        scale_input = st.selectbox(
            '스케일',
            ['', 'student', 'research', 'industry'],
            index=0,
            format_func=lambda x: '선택 예: student / research / industry' if x == '' else SCALE_LABELS.get(x, x)
        )
        purpose_input = st.text_input('용도', value='', placeholder='예: 학생용 공 수집 및 발사 로봇')
        mass_input = st.text_input('질량 (kg)', value='', placeholder='예: 55')
        speed_input = st.text_input('속도', value='', placeholder='예: 2.0')
        unit_input = st.selectbox('단위', ['', 'mps', 'kmh'], index=0, format_func=lambda x: '선택 예: mps 또는 kmh' if x == '' else UNIT_LABELS.get(x, x))
        wheels_input = st.text_input('구동 바퀴 수', value='', placeholder='예: 4')
        env_input = st.selectbox(
            '환경',
            ['', 'indoor', 'normal', 'obstacle', 'extreme'],
            index=0,
            format_func=lambda x: '선택 예: indoor / obstacle / extreme' if x == '' else ENV_LABELS.get(x, x)
        )
        extra_input = st.text_area('기타 요구사항 (상세할수록 구체화)', value='', placeholder='예: intake, feeder, shooter, 알루미늄 프로파일, 3D 프린팅 브라켓')

        data = dict(
            scale=scale_input if scale_input else 'student',
            purpose=purpose_input.strip() if purpose_input.strip() else '학생용 이동 로봇',
            mass=parse_float(mass_input, 35.0),
            speed=parse_float(speed_input, 1.5),
            unit=unit_input if unit_input else 'mps',
            wheels=parse_int(wheels_input, 4),
            env=env_input if env_input else 'indoor',
            extra=extra_input.strip() if extra_input.strip() else '없음'
        )

part, rows, calc = analyze(data)

# =========================================================
# 1. 물리 모델 분석
# =========================================================
st.subheader("1. 물리 모델 역산 결과")
col1, col2, col3, col4 = st.columns(4)
col1.metric("요구 동력", f"{calc['req_power']:.0f} W")
col2.metric("바퀴당 요구 토크", f"{calc['req_tq']:.2f} Nm")
col3.metric("필요 휠 RPM", f"{calc['req_rpm']:.1f} RPM")
col4.metric("적용 경사각", f"{calc['grade']}°")

with st.container(border=True):
    st.markdown("**추천 주행 모터 정보**")
    st.write(f"- 모델/계열: **{part['motor_name']}**")
    st.write(f"- 주요 사양: {part['motor_spec']}")
    st.write(f"- 역산 기준 토크: 약 **{calc['motor_nm']:.2f} Nm**")

# =========================================================
# 2. 기어비 후보 분석
# =========================================================
st.subheader("2. 기어비 후보 분석")
gear_table = []
for i, r in enumerate(rows, 1):
    gear_table.append({
        "순위": f"{i}위",
        "추천도": stars(r['stars']),
        "기어비": f"{r['ratio']}:1",
        "기어 잇수": f"20T : {r['driven']}T",
        "예상 휠 RPM": f"{r['rpm']:.1f}",
        "예상 토크": f"{r['tq']:.2f} Nm",
        "유형": r['typ'],
        "추천 이유": r['reason']
    })
st.table(gear_table)

st.info("표는 목표 휠 RPM에 가까운 정도와 토크 여유를 함께 반영해 정렬됩니다. 빠른 이동이 중요하면 속도형, 등판·하중이 중요하면 토크형, 첫 제작 기준안은 균형형을 우선 검토하세요.")

# =========================================================
# 3. 예산안
# =========================================================
st.subheader("3. 정밀 예산안")
budget_raw = [
    ('주행 구동부', part['motor_name'], part['motor_spec'], part['motor_cost'], data['wheels']),
    ('주행 구동부', part['gear_name'], part['gear_spec'], part['gear_cost'], data['wheels']),
    ('바퀴/축/베어링', part['wheel_name'], part['wheel_spec'], part['wheel_cost'], data['wheels']),
    ('제어/전원부', part['control_name'], part['control_spec'], part['control_cost'], 1),
    ('주요 구성 형체', part['frame_name'], part['frame_spec'], part['frame_cost'], 1),
]
for item in aux_items(data['extra']):
    cat, name, spec, unit_cost, qty, role = item
    budget_raw.append((cat, name, f"{spec} / 역할: {role}", unit_cost, qty))

budget_rows = []
for cat, name, spec, unit_cost, qty in budget_raw:
    budget_rows.append({
        "분류": cat,
        "품목": name,
        "규격/근거": spec,
        "단가": f"{unit_cost:,}원",
        "수량": qty,
        "합계": f"{unit_cost * qty:,}원"
    })

total = sum(unit_cost * qty for _, _, _, unit_cost, qty in budget_raw)
st.table(budget_rows)
st.success(f"총 예상 제작 비용: 약 {total:,}원")
st.caption("※ 단가는 초기 예산 가늠을 위한 기준값입니다. 실제 구매처, 배송비, 가공 방식, 수량, 환율에 따라 달라질 수 있습니다.")

# =========================================================
# 4. Fusion 360 기어 도면 & 가이드
# =========================================================
st.subheader("4. Fusion 360 기어 도면 & 초기 설계 가이드")
if rows:
    best = rows[0]
    c1, c2 = st.columns([1, 1])
    fig, module, center_dist, driven_teeth = draw_fusion_gear_guide(best['ratio'], data['mass'])
    with c1:
        if fig:
            st.pyplot(fig)
    with c2:
        st.markdown("**초기 스케치 가이드**")
        st.write(f"1. 중심 거리: 기어 모듈 {module:.1f} 기준, 두 축 간 거리는 약 **{center_dist:.1f}mm**로 스케치하세요.")
        st.write(f"2. 조인트(Fusion360): 모터와 바퀴에 Revolute 적용 후 Motion Link를 **360도 : {360 / best['ratio']:.1f}도**로 설정하세요.")
        st.write("3. 3D프린터 출력 팁: 구멍 공차는 도면보다 **+0.2mm** 크게 잡으면 조립이 수월합니다.")
        st.write("4. 프레임 기준면을 먼저 잡고, 모터 마운트 → 축 위치 → 바퀴/기어 위치 → 보조 장치 순서로 배치하면 설계 수정이 쉽습니다.")

# =========================================================
# 5. 시스템 개념 스케치 및 설명
# =========================================================
st.subheader("5. 초기 아이디어 스케치")
if rows:
    draw_sketch(data, part, rows[0])

st.markdown("**구조물과 장치의 유기적 역할 및 실행 프로세스**")
st.write(process_description(data, part, rows, calc))

# =========================================================
# 6. 테스트베드 복사용 요약
# =========================================================
st.subheader("6. 테스트베드 붙여넣기용 전체 요약")
summary_text = build_testbed_text(data, part, rows, calc, budget_rows, total)
st.text_area("아래 내용을 복사해 테스트베드/보고서/노션 등에 붙여넣을 수 있습니다.", value=summary_text, height=300)

# Streamlit 기본 기능으로 복사 버튼에 준하는 다운로드 제공
st.download_button(
    label="📋 전체 요약 텍스트 다운로드",
    data=summary_text,
    file_name="mobility_design_summary.txt",
    mime="text/plain"
)

# HTML/JS 기반 클립보드 복사 버튼
escaped = summary_text.replace('`', '\\`').replace('\\', '\\\\')
st.components.v1.html(f"""
<button onclick="navigator.clipboard.writeText(`{escaped}`).then(() => alert('전체 요약이 클립보드에 복사되었습니다.'))" 
style="padding:10px 16px; border:0; border-radius:8px; background:#2563eb; color:white; font-weight:700; cursor:pointer;">
📋 전체 내용 한 번에 복사하기
</button>
""", height=60)

