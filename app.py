import math
import html
import textwrap
import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 웹 페이지 제목 설정
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

ENV_LABELS = {
    'normal': '단순 이동/평지 중심',
    'indoor': '실내 자율 이동/완만한 경사',
    'obstacle': '장애물 많은 지형/요철',
    'extreme': '험한 지형/급경사·비포장',
}

SCALE_LABELS = {
    'student': '학생용/공모전·탐구',
    'research': '연구용/실험·시제품',
    'industry': '산업용/고하중·전문 장비',
}


def env_grade(env):
    return {'normal': 2, 'indoor': 8, 'obstacle': 15, 'extreme': 35}.get(env, 8)


def classify_parts(req_power, scale):
    if req_power <= 60 and scale != 'industry':
        return dict(tier='소형', wheel_r=0.05, motor_rpm=4000, motor_nm=0.10,
            motor='Parvalux PBL42 Range BLDC 모터 · 24~48V · 4000rpm · 26~42W · 연속토크 0.06~0.10Nm', motor_cost=85000,
            gear='미스미 소모듈 평기어 M0.8~1.0 · 압력각 20° · C3604 황동 또는 POM', gear_cost=18000,
            wheel='100mm 우레탄/고무 로봇 바퀴 + Ø6mm SUS304 축 + 소형 베어링', wheel_cost=18000,
            control='Arduino/ESP32 제어보드 + 소형 DC/BLDC 드라이버 + 12~24V 배터리', control_cost=120000,
            frame='PLA/PETG 3D 프린팅 브라켓 + 소형 알루미늄 프로파일', frame_cost=90000)
    if req_power <= 220 and scale != 'industry':
        return dict(tier='중소형', wheel_r=0.10, motor_rpm=3000, motor_nm=0.50,
            motor='Parvalux PBL60 Range BLDC 모터 · 24~48V · 3000rpm · 104~157W · 연속토크 0.33~0.50Nm', motor_cost=240000,
            gear='PGx42/GB28급 기어헤드 또는 미스미 평기어 M2.0 S45C', gear_cost=65000,
            wheel='200mm 솔리드 우레탄 바퀴 + Ø10mm S45C 축 + 플랜지 베어링', wheel_cost=55000,
            control='24V BLDC 드라이버 2~4ch + 24V 10~20Ah 리튬 배터리 + 퓨즈', control_cost=420000,
            frame='2020/3030 알루미늄 프로파일 프레임 + 3D프린팅 모터마운트', frame_cost=180000)
    if req_power <= 650 or scale == 'research':
        return dict(tier='중형', wheel_r=0.12, motor_rpm=4000, motor_nm=1.40,
            motor='Parvalux PBL86 Range BLDC 모터 · 48V · 4000rpm · 419~586W · 연속토크 1.00~1.40Nm', motor_cost=480000,
            gear='Parvalux PGx70/PGx52 기어박스 또는 미스미 경제형 평기어 M3.0 · GB/T 10095 8등급', gear_cost=101396,
            wheel='250mm 고하중 우레탄 바퀴 + Ø15mm S45C 열처리 축 + 하우징 베어링', wheel_cost=95000,
            control='48V BLDC 드라이버 + 48V 20Ah 배터리팩 + BMS + 비상정지 스위치', control_cost=900000,
            frame='3030/4040 알루미늄 프로파일 또는 절곡 알루미늄 판재 섀시', frame_cost=350000)
    return dict(tier='대형', wheel_r=0.25, motor_rpm=3000, motor_nm=8.00,
        motor='AC 서보모터 SD13/SD48급 또는 산업용 BLDC 서보 · 1kW 이상급 · 인버터 제어', motor_cost=1200000,
        gear='헬리컬/웜 감속기 또는 LIW/MWS급 고토크 기어헤드 · 28~45Nm급 이상', gear_cost=850000,
        wheel='13인치 이상 튜브/솔리드 타이어 + Ø20mm 이상 구동축 + 자동차형 베어링', wheel_cost=220000,
        control='서보 드라이브/인버터 + 48V~고전압 배터리팩 + BMS + 차단기', control_cost=3500000,
        frame='강철 사각파이프 용접 프레임 또는 주문제작 절곡 섀시', frame_cost=2200000)


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
    if has('waterwheel', '워터휠'):
        items.append(('보조 기구부', 'Waterwheel/색인 휠용 AC/BLDC 보조모터 + 원판형 휠', 120000, 1, '공 또는 물체의 방향과 공급 순서를 제어'))
    if has('lift', '리프트', '엘리베이터'):
        items.append(('보조 기구부', 'Lift 승강용 웜기어드 모터 + 리니어 가이드 + 랙기어', 160000, 1, '상하 이동 또는 높이 조절 기능 수행'))
    if has('lidar', '라이다', '카메라', '센서'):
        items.append(('센서/인식부', '2D LiDAR/카메라/초음파 센서 묶음 + 마운트', 220000, 1, '자율 이동과 장애물 인식'))
    if has('트랙', '궤도', 'track'):
        items.append(('주행 보강부', '소형 무한궤도 트랙 키트 또는 고무 트랙 벨트 세트', 180000, 2, '접지 면적을 늘려 험지 주행 안정성 향상'))
    return items


def stars(n):
    return '★' * n + '☆' * (5 - n)


def analyze(data):
    scale, mass, speed, unit, wheels, env, extra = data['scale'], data['mass'], data['speed'], data['unit'], data['wheels'], data['env'], data['extra']
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
    for r in [3, 4, 5, 6, 8]:
        if len(ratios) >= 5:
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
    return part, rows, dict(speed_mps=speed_mps, grade=grade, req_power=req_power, req_tq=req_tq, req_rpm=req_rpm, motor_nm=motor_nm)


def is_track_type(data):
    e = data.get('extra', '').lower()
    p = data.get('purpose', '').lower()
    return ('궤도' in data.get('extra', '') or '트랙' in data.get('extra', '') or 'track' in e or '궤도' in data.get('purpose', '') or '탐사' in p)


def is_scooter_type(data):
    p = data.get('purpose', '').lower()
    return '킥보드' in data.get('purpose', '') or 'scooter' in p


def is_car_type(data):
    p = data.get('purpose', '').lower()
    return '전기차' in data.get('purpose', '') or '차형' in data.get('purpose', '') or 'car' in p


def draw_label(ax, text, xy, xytext, color='#294a7a'):
    """Streamlit Cloud의 한글 폰트 깨짐을 피하기 위해 도면 내부 라벨은 영문 중심으로 표시한다."""
    ax.annotate(
        text,
        xy=xy,
        xytext=xytext,
        arrowprops=dict(arrowstyle='->', color=color, lw=2.0, shrinkA=4, shrinkB=4),
        color=color,
        fontsize=10,
        fontweight='bold',
        ha='center',
        va='center',
        bbox=dict(boxstyle='round,pad=0.22', fc='white', ec=color, lw=1.2, alpha=0.95)
    )


def draw_wheel(ax, x, y, r, red):
    ax.add_patch(patches.Circle((x, y), r, fill=False, edgecolor=red, lw=4.0))
    ax.add_patch(patches.Circle((x, y), r * 0.45, fill=False, edgecolor=red, lw=3.0))
    ax.plot([x - r * 0.7, x + r * 0.7], [y, y], color=red, lw=2.0)
    ax.plot([x, x], [y - r * 0.7, y + r * 0.7], color=red, lw=2.0)


def draw_initial_layout_sketch(data, part, best):
    """
    첨부된 '초기 배치 스케치' 자료처럼,
    완성 외형 렌더링이 아니라 빨간 구조선 + 파란 주요 장치 박스 + 화살표 메모 중심의 초기 배치도 생성.
    도면 내부의 한글 깨짐을 막기 위해 내부 라벨은 영문으로 표기하고, 아래 설명에서 한국어로 대응시킨다.
    """
    try:
        fig, ax = plt.subplots(figsize=(11, 5.6), dpi=130)
        ax.set_xlim(0, 1100)
        ax.set_ylim(650, 0)
        ax.axis('off')
        ax.set_facecolor('white')
        fig.patch.set_facecolor('white')

        red = '#c9362f'
        blue = '#2b4d83'
        purple = '#7a45e5'
        lw = 4.0

        # 제목은 영문으로 간단히 처리해 폰트 깨짐 방지
        ax.text(55, 58, 'Initial Layout Sketch', fontsize=17, fontweight='bold', color='#1f2937')
        ax.text(55, 86, data['purpose'][:55], fontsize=10, color='#374151')

        track = is_track_type(data)
        scooter = is_scooter_type(data)
        car = is_car_type(data)
        e = data.get('extra', '').lower()

        # -------- 1) 기본 뼈대: 목적에 따라 외형 뼈대만 달리함 --------
        if scooter:
            # 킥보드형: 데크 + 핸들바 + 2륜
            ax.plot([230, 820], [430, 430], color=red, lw=lw)
            ax.plot([760, 800, 825], [430, 285, 275], color=red, lw=lw)
            ax.plot([825, 855], [275, 275], color=red, lw=lw)
            ax.add_patch(patches.Rectangle((360, 375), 200, 46, fill=False, edgecolor=blue, lw=3.0))
            draw_wheel(ax, 265, 505, 55, red)
            draw_wheel(ax, 780, 505, 55, red)
            motor_xy = (265, 445)
            battery_xy = (460, 398)
        elif car:
            # 자동차형: 낮은 차체 + 캐빈 + 4륜 느낌
            ax.plot([170, 255, 820, 920, 860, 230, 170], [430, 305, 305, 430, 505, 505, 430], color=red, lw=lw)
            ax.plot([330, 735], [320, 495], color=red, lw=2.8)
            ax.plot([725, 345], [320, 495], color=red, lw=2.8)
            draw_wheel(ax, 300, 525, 58, red)
            draw_wheel(ax, 790, 525, 58, red)
            ax.add_patch(patches.Rectangle((430, 410), 180, 55, fill=False, edgecolor=blue, lw=3.0))
            motor_xy = (300, 455)
            battery_xy = (520, 438)
        elif track:
            # 궤도형: 단순 사다리꼴 차체 + 트랙
            ax.plot([210, 315, 765, 875, 815, 245, 210], [420, 285, 285, 420, 500, 500, 420], color=red, lw=lw)
            ax.add_patch(patches.FancyBboxPatch((185, 465), 700, 100, boxstyle='round,pad=0,rounding_size=52', fill=False, edgecolor=red, lw=4.0))
            draw_wheel(ax, 285, 515, 42, red)
            draw_wheel(ax, 515, 525, 36, red)
            draw_wheel(ax, 770, 515, 42, red)
            ax.add_patch(patches.Rectangle((425, 385), 185, 60, fill=False, edgecolor=blue, lw=3.0))
            motor_xy = (285, 455)
            battery_xy = (518, 415)
        else:
            # 일반 로봇/대회형: 첨부 예시처럼 상부 프레임 + 하부 프레임 + 2D 바퀴
            ax.plot([185, 290, 760, 875, 820, 235, 185], [425, 285, 285, 425, 505, 505, 425], color=red, lw=lw)
            ax.plot([290, 760], [425, 425], color=red, lw=lw)
            ax.plot([360, 700], [300, 485], color=red, lw=2.8)
            ax.plot([700, 360], [300, 485], color=red, lw=2.8)
            draw_wheel(ax, 275, 535, 58, red)
            draw_wheel(ax, 805, 535, 58, red)
            if int(data.get('wheels', 4)) >= 6:
                draw_wheel(ax, 535, 540, 45, red)
            ax.add_patch(patches.Rectangle((225, 430), 135, 52, fill=False, edgecolor=blue, lw=3.0))
            ax.add_patch(patches.Circle((390, 456), 28, fill=False, edgecolor=blue, lw=3.0))
            ax.add_patch(patches.Rectangle((500, 395), 190, 62, fill=False, edgecolor=blue, lw=3.0))
            motor_xy = (285, 456)
            battery_xy = (595, 426)

        # -------- 2) 공통 주요 구동 장치 --------
        if not (not track and not scooter and not car):
            ax.add_patch(patches.Rectangle((215, 420), 130, 50, fill=False, edgecolor=blue, lw=3.0))
            ax.add_patch(patches.Circle((375, 445), 25, fill=False, edgecolor=blue, lw=3.0))
        ax.text(motor_xy[0] - 45, motor_xy[1] - 28, 'M', fontsize=14, color=blue, fontweight='bold')
        ax.text(motor_xy[0] + 35, motor_xy[1] + 20, f'{int(best["ratio"])}:1 Gear', fontsize=10, color=red, fontweight='bold')
        draw_label(ax, 'Drive Motor', xy=motor_xy, xytext=(125, 585), color=blue)
        draw_label(ax, 'Gearbox', xy=(motor_xy[0] + 95, motor_xy[1]), xytext=(225, 620), color=blue)
        draw_label(ax, 'Battery / Controller', xy=battery_xy, xytext=(560, 610), color=blue)

        # -------- 3) 기타 요구사항 기반 보조 장치 배치 --------
        if 'intake' in e or '인테이크' in data.get('extra', ''):
            ax.add_patch(patches.Rectangle((825, 405), 120, 75, fill=False, edgecolor=purple, lw=3.2))
            ax.add_patch(patches.Circle((835, 485), 14, fill=False, edgecolor=purple, lw=2.0))
            draw_label(ax, 'Intake Motor', xy=(885, 442), xytext=(955, 585), color=purple)
        if 'feeder' in e or '피더' in data.get('extra', ''):
            ax.add_patch(patches.Rectangle((415, 335), 120, 52, fill=False, edgecolor=purple, lw=3.0))
            draw_label(ax, 'Feeder Motor', xy=(475, 360), xytext=(330, 250), color=purple)
        if 'shooter' in e or '슈터' in data.get('extra', ''):
            ax.add_patch(patches.Rectangle((655, 145), 150, 90, fill=False, edgecolor=purple, lw=3.4))
            ax.add_patch(patches.Circle((685, 190), 22, fill=False, edgecolor=purple, lw=2.4))
            ax.add_patch(patches.Circle((765, 190), 22, fill=False, edgecolor=purple, lw=2.4))
            draw_label(ax, 'Shooter Motors', xy=(730, 170), xytext=(880, 120), color=purple)
        if 'waterwheel' in e or '워터휠' in data.get('extra', ''):
            ax.add_patch(patches.Circle((620, 330), 38, fill=False, edgecolor=purple, lw=3.0))
            for a in [0, 60, 120]:
                x2 = 620 + 38 * math.cos(math.radians(a))
                y2 = 330 + 38 * math.sin(math.radians(a))
                ax.plot([620, x2], [330, y2], color=purple, lw=2.0)
            draw_label(ax, 'Index Wheel', xy=(655, 330), xytext=(830, 330), color=purple)
        if 'lift' in e or '리프트' in data.get('extra', '') or '엘리베이터' in data.get('extra', ''):
            ax.add_patch(patches.Rectangle((120, 255), 65, 210, fill=False, edgecolor=purple, lw=3.0))
            ax.plot([152, 152], [275, 445], color=purple, lw=2.0)
            draw_label(ax, 'Lift Motor', xy=(152, 330), xytext=(70, 190), color=purple)
        if '카메라' in data.get('extra', '') or 'camera' in e or 'lidar' in e or '라이다' in data.get('extra', ''):
            ax.add_patch(patches.Rectangle((505, 210), 80, 48, fill=False, edgecolor=purple, lw=3.0))
            draw_label(ax, 'Sensor', xy=(545, 232), xytext=(490, 145), color=purple)

        # 바닥 기준선은 스케치 느낌으로만 짧게
        ax.plot([160, 930], [595, 595], color='#9ca3af', lw=1.5)
        ax.text(805, 626, 'simple placement sketch, not final CAD', fontsize=9, color='#6b7280')

        plt.tight_layout()
        st.pyplot(fig, clear_figure=True)
    except Exception as e:
        st.warning(f'스케치 표시 중 오류 발생: {e}')


def process_description(data, part, best, calc):
    aux = aux_items(data.get('extra', ''))
    aux_names = [item[1].split()[0] for item in aux]
    lines = []
    lines.append(f"이 스케치는 최종 외형이 아니라, {data['purpose']}의 주요 장치를 어느 위치에 배치할지 정하는 초기 배치도입니다.")
    lines.append(f"주행 구동부는 {part['motor']}를 기준으로 하며, 모터 회전은 {best['ratio']}:1 감속기를 거쳐 바퀴/트랙 축으로 전달됩니다. 이때 감속기는 속도를 낮추는 대신 바퀴 토크를 키워 출발, 등판, 장애물 통과에 필요한 힘을 확보합니다.")
    lines.append("배터리와 제어기는 차체 중앙부에 배치하는 것이 기본입니다. 중앙 배치는 무게중심을 안정시키고, 좌우 구동 모터까지의 배선을 짧게 만들어 전압강하와 배선 복잡도를 줄이는 데 유리합니다.")
    if aux:
        roles = []
        for cat, name, unit, qty, role in aux:
            roles.append(f"- {name}: {role}")
        lines.append("기타 요구사항에서 감지된 보조 장치의 역할은 다음과 같습니다.\n" + "\n".join(roles))
        lines.append("실행 프로세스는 대체로 '주행 구동부로 위치 이동 → 인테이크/센서 등으로 대상 감지·수집 → 피더/워터휠로 정렬·이송 → 슈터/리프트 등 최종 장치로 기능 수행' 순서로 구성할 수 있습니다.")
    else:
        lines.append("현재 기타 구동부가 명시되지 않았으므로, 기본 실행 프로세스는 '제어기 명령 → 주행 모터 구동 → 감속기 토크 증폭 → 바퀴/트랙 회전 → 목표 지형 이동' 순서로 볼 수 있습니다.")
    lines.append(f"계산상 요구 동력은 약 {calc['req_power']:.0f}W, 바퀴당 요구 토크는 약 {calc['req_tq']:.2f}Nm입니다. 따라서 실제 제작 시에는 표의 1순위뿐 아니라 토크 여유가 큰 후보도 함께 검토하는 것이 좋습니다.")
    return "\n\n".join(lines)


def fusion_guide(data, part, best):
    module = 1.0 if data['mass'] <= 30 else (2.0 if data['mass'] <= 400 else 3.0)
    drive_teeth = 20
    driven_teeth = int(best['driven'])
    center_dist = (drive_teeth + driven_teeth) * module / 2
    motion_link = 360 / best['ratio']
    return module, center_dist, motion_link, f"""
1. 중심 거리: 기어 모듈 {module:.1f} 기준, 구동기어 {drive_teeth}T와 피동기어 {driven_teeth}T의 두 축 간 거리는 약 {center_dist:.1f}mm로 스케치하세요.
2. 조인트(Fusion 360): 모터축과 바퀴축에 각각 Revolute Joint를 적용한 뒤 Motion Link를 360도 : {motion_link:.1f}도로 설정하세요.
3. 3D프린터 출력 팁: 모터 마운트와 축 구멍은 도면보다 +0.2mm 정도 크게 잡으면 조립이 수월합니다.
4. 배치 팁: 배터리/제어기는 중앙, 모터/감속기는 바퀴 가까이 배치하면 무게중심과 배선 정리가 쉬워집니다.
""".strip()


def draw_fusion_gear_diagram(best, data):
    fig, ax = plt.subplots(figsize=(7.5, 3.8), dpi=130)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    module, center_dist, motion_link, _ = fusion_guide(data, classify_parts(1, data['scale']), best)
    drive_teeth = 20
    driven_teeth = int(best['driven'])
    r1 = drive_teeth * module / 2
    r2 = driven_teeth * module / 2
    c1 = (0, 0)
    c2 = (r1 + r2, 0)
    ax.add_patch(patches.Circle(c1, r1, fill=False, edgecolor='#2563eb', lw=2.5, linestyle='--'))
    ax.add_patch(patches.Circle(c2, r2, fill=False, edgecolor='#dc2626', lw=2.5, linestyle='--'))
    ax.plot([c1[0], c2[0]], [0, 0], color='#111827', lw=1.4, linestyle='-.')
    ax.plot(c1[0], c1[1], 'o', color='#111827')
    ax.plot(c2[0], c2[1], 'o', color='#111827')
    ax.text(c1[0], -r1-7, 'Motor gear 20T', ha='center', fontsize=9, color='#2563eb')
    ax.text(c2[0], -r2-7, f'Wheel gear {driven_teeth}T', ha='center', fontsize=9, color='#dc2626')
    ax.text((c1[0]+c2[0])/2, 8, f'Center distance {center_dist:.1f} mm', ha='center', fontsize=9, color='#111827')
    lim = r1 + r2 + max(r1, r2) * 0.45 + 12
    ax.set_xlim(-r1-15, c2[0]+r2+15)
    ax.set_ylim(-max(r1, r2)-20, max(r1, r2)+20)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)


def safe_float(text, default):
    try:
        if text is None or str(text).strip() == '':
            return default
        return float(text)
    except ValueError:
        return default


def safe_int(text, default):
    try:
        if text is None or str(text).strip() == '':
            return default
        return int(float(text))
    except ValueError:
        return default


def build_report_text(data, part, rows, calc, total, budget):
    best = rows[0]
    budget_lines = []
    for cat, name, unit, qty, *role in budget:
        budget_lines.append(f"- {cat}: {name} / 단가 {unit:,}원 × {qty}개 = {unit*qty:,}원")
    return f"""
모빌리티 구동계 초기 설계 도움 시스템 결과 요약

[입력 조건]
- 제작 스케일: {SCALE_LABELS.get(data['scale'], data['scale'])}
- 용도: {data['purpose']}
- 질량: {data['mass']} kg
- 목표 속도: {data['speed']} {data['unit']}
- 구동 바퀴 수: {data['wheels']}개
- 운행 환경: {ENV_LABELS.get(data['env'], data['env'])}
- 기타 요구사항: {data['extra']}

[물리 모델 결과]
- 요구 동력: 약 {calc['req_power']:.0f} W
- 바퀴당 요구 토크: 약 {calc['req_tq']:.2f} Nm
- 필요 휠 RPM: 약 {calc['req_rpm']:.1f} RPM
- 추천 모터: {part['motor']}

[추천 기어비]
- 1순위: {best['ratio']}:1, 20T:{best['driven']}T, 예상 휠 RPM {best['rpm']:.1f}, 예상 휠 토크 {best['tq']:.2f}Nm
- 선정 이유: {best['reason']}

[예산안]
{chr(10).join(budget_lines)}
- 총 예상 제작 비용: 약 {total:,}원

[초기 배치 스케치 해석]
{process_description(data, part, best, calc)}
""".strip()


# Streamlit 웹 화면 구성
st.title("⚙️ 모빌리티 구동계 초기 설계 도움 시스템")
st.caption("제작자가 탐구와 설계를 시작할 수 있도록 물리 계산 기반 초기 후보안, 기어비, 부품, 예산, 초기 배치 스케치를 제공합니다.")

with st.sidebar:
    st.header("입력 방식")
    option_list = ["직접 입력"] + [f"{k}. {v['purpose']} ({v['mass']}kg)" for k, v in PRESETS.items()]
    selected_option = st.selectbox("빠른 설정 또는 직접 입력", option_list)

    if selected_option != "직접 입력":
        preset_key = int(selected_option.split(".")[0])
        data = PRESETS[preset_key].copy()
        st.success(f"{preset_key}. {data['purpose']} 프리셋을 불러왔습니다.")
    else:
        st.subheader("직접 상세 조건 입력")
        st.caption("입력란은 처음에는 비어 있습니다. 비워두면 내부 기본값으로 계산됩니다.")
        scale_raw = st.selectbox('스케일/용도', ['', 'student', 'research', 'industry'], format_func=lambda x: '선택하세요' if x == '' else SCALE_LABELS.get(x, x))
        purpose_raw = st.text_input('모빌리티 용도', value='', placeholder='예: 대회용 공 수집 및 발사 로봇')
        mass_raw = st.text_input('질량 (kg)', value='', placeholder='예: 55')
        speed_raw = st.text_input('목표 속도', value='', placeholder='예: 2.0')
        unit_raw = st.selectbox('속도 단위', ['', 'mps', 'kmh'], format_func=lambda x: '선택하세요' if x == '' else ('m/s' if x == 'mps' else 'km/h'))
        wheels_raw = st.text_input('구동 바퀴 수', value='', placeholder='예: 4')
        env_raw = st.selectbox('운행 환경', ['', 'normal', 'indoor', 'obstacle', 'extreme'], format_func=lambda x: '선택하세요' if x == '' else ENV_LABELS.get(x, x))
        extra_raw = st.text_area('기타 요구사항 (상세할수록 구체화)', value='', placeholder='예: intake, feeder, shooter, waterwheel, 알루미늄 프로파일, 3D프린팅 브라켓')

        data = dict(
            scale=scale_raw if scale_raw else 'student',
            purpose=purpose_raw.strip() if purpose_raw.strip() else '학생용 이동 로봇',
            mass=safe_float(mass_raw, 35.0),
            speed=safe_float(speed_raw, 1.5),
            unit=unit_raw if unit_raw else 'mps',
            wheels=max(1, safe_int(wheels_raw, 4)),
            env=env_raw if env_raw else 'indoor',
            extra=extra_raw.strip() if extra_raw.strip() else '없음'
        )

part, rows, calc = analyze(data)
best = rows[0]

st.subheader("1. 물리 모델 분석 결과")
col1, col2, col3, col4 = st.columns(4)
col1.metric("요구 동력", f"{calc['req_power']:.0f} W")
col2.metric("바퀴당 요구 토크", f"{calc['req_tq']:.2f} Nm")
col3.metric("필요 휠 RPM", f"{calc['req_rpm']:.1f} RPM")
col4.metric("적용 환경", f"{calc['grade']}° 상당")
st.info(f"**추천 모터:** {part['motor']}  /  계산 기준 토크: {calc['motor_nm']:.2f} Nm")

st.subheader("2. 기어비 후보 분석")
st.table([
    {
        "순위/추천도": f"{i}위 {stars(r['stars'])}",
        "기어비": f"{r['ratio']}:1",
        "기어 잇수": f"20T:{r['driven']}T",
        "예상 휠 RPM": f"{r['rpm']:.1f}",
        "예상 휠 토크": f"{r['tq']:.2f} Nm",
        "유형": r['typ'],
        "선정 이유": r['reason']
    } for i, r in enumerate(rows, 1)
])
st.caption("별점은 목표 휠 RPM과의 근접성, 요구 토크 대비 여유, 속도/힘 균형을 함께 고려해 매깁니다. 빠른 이동이 중요하면 속도형, 험지·하중이 중요하면 토크형 후보도 검토하세요.")

st.subheader("3. 정밀 예산안")
budget = [
    ('주행 구동부', part['motor'], part['motor_cost'], data['wheels']),
    ('주행 구동부', part['gear'], part['gear_cost'], data['wheels']),
    ('바퀴/축/베어링', part['wheel'], part['wheel_cost'], data['wheels']),
    ('제어/전원부', part['control'], part['control_cost'], 1),
    ('주요 구성 형체', part['frame'], part['frame_cost'], 1)
] + aux_items(data['extra'])

total = sum(x[2] * x[3] for x in budget)
st.table([
    {
        "분류": cat,
        "상세 품명 및 규격": name,
        "단가": f"{unit:,}원",
        "수량": qty,
        "소계": f"{unit * qty:,}원",
        "역할": role[0] if role else "-"
    }
    for cat, name, unit, qty, *role in budget
])
st.success(f"**총 예상 제작 비용: 약 {total:,}원**")
st.caption("※ 예산은 초기 설계 단계의 추정값입니다. 실제 구매처, 배송비, 가공비, 예비 부품, 공구 보유 여부에 따라 달라질 수 있습니다.")

st.subheader("4. Fusion 360 기어 도면 & 초기 설계 가이드")
f_col1, f_col2 = st.columns([1.05, 1])
with f_col1:
    draw_fusion_gear_diagram(best, data)
with f_col2:
    _, _, _, guide_text = fusion_guide(data, part, best)
    st.markdown("**초기 스케치 가이드**")
    st.write(guide_text)

st.subheader("5. 초기 배치 스케치")
st.caption("도면 내부 라벨은 Streamlit Cloud의 한글 폰트 깨짐을 피하기 위해 영문으로 표시했습니다. 아래 설명에서 한국어 의미를 함께 제공합니다.")
draw_initial_layout_sketch(data, part, best)

st.markdown("**스케치 라벨 해석**")
st.markdown("- **Drive Motor**: 주행 모터, 바퀴 또는 트랙을 돌리는 핵심 구동원\n- **Gearbox**: 감속기/기어부, 모터 회전수를 낮추고 토크를 키우는 장치\n- **Battery / Controller**: 배터리와 제어기, 전체 모터에 전력과 제어 신호를 공급\n- **Intake / Feeder / Shooter / Index Wheel / Lift**: 기타 요구사항에 따라 추가되는 보조 구동부")

st.markdown("**구조물과 장치들의 유기적 역할 및 실행 프로세스**")
st.write(process_description(data, part, best, calc))

report_text = build_report_text(data, part, rows, calc, total, budget)
st.subheader("6. 테스트베드/보고서 붙여넣기용 전체 요약")
st.code(report_text, language="markdown")
escaped_report = html.escape(report_text).replace("\n", "\\n").replace("'", "&#39;")
components.html(
    f"""
    <button onclick="navigator.clipboard.writeText('{escaped_report}').then(() => alert('전체 요약이 복사되었습니다.'))"
      style="background:#2563eb;color:white;border:none;border-radius:8px;padding:10px 16px;font-weight:700;cursor:pointer;">
      전체 요약 복사하기
    </button>
    """,
    height=55,
)
st.download_button("텍스트 파일로 저장", data=report_text, file_name="mobility_design_summary.txt", mime="text/plain")

