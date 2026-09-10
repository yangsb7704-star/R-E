import math
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 웹 페이지 제목 설정
st.set_page_config(page_title="모빌리티 구동계 설계 최적화", layout="wide")

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
    def has(*ks): return any(k.lower() in e or k in extra for k in ks)
    if has('intake', '인테이크'): items.append(('보조 기구부', 'Intake 흡입 롤러용 775/550급 DC 모터 또는 소형 BLDC + 고무 롤러 + 벨트', 95000, 1, '바닥의 공/물체를 로봇 내부로 끌어올림'))
    if has('feeder', '피더'): items.append(('보조 기구부', 'Feeder 이송용 서보모터/기어드 DC 모터 + 타이밍벨트 풀리', 80000, 1, '수집된 물체를 슈터나 저장부로 일정하게 공급'))
    if has('shooter', '슈터'): items.append(('보조 기구부', 'Shooter 고속 플라이휠용 BLDC/DC 모터 2개 + 플라이휠 + 모터 브라켓', 140000, 2, '고속 회전 휠로 공을 목표 방향으로 발사'))
    if has('waterwheel', '워터휠'): items.append(('보조 기구부', 'Waterwheel/색인 휠용 AC/BLDC 보조모터 + 원판형 휠', 120000, 1, '공 또는 물체의 방향과 공급 순서를 제어'))
    if has('lift', '리프트', '엘리베이터'): items.append(('보조 기구부', 'Lift 승강용 웜기어드 모터 + 리니어 가이드 + 랙기어', 160000, 1, '상하 이동 또는 높이 조절 기능 수행'))
    if has('lidar', '라이다', '카메라', '센서'): items.append(('센서/인식부', '2D LiDAR/카메라/초음파 센서 묶음 + 마운트', 220000, 1, '자율 이동과 장애물 인식'))
    if has('트랙', '궤도', 'track'): items.append(('주행 보강부', '소형 무한궤도 트랙 키트 또는 고무 트랙 벨트 세트', 180000, 2, '접지 면적을 늘려 험지 주행 안정성 향상'))
    return items

def stars(n): return '★'*n + '☆'*(5-n)

def analyze(data):
    scale, mass, speed, unit, wheels, env, extra = data['scale'], data['mass'], data['speed'], data['unit'], data['wheels'], data['env'], data['extra']
    speed_mps = speed/3.6 if unit == 'kmh' else speed
    grade = env_grade(env)
    g, crr, sf, eff = 9.81, 0.02, 1.5, 0.85
    base_res = crr*mass*g*math.cos(math.radians(grade)) + mass*g*math.sin(math.radians(grade))
    req_force = base_res*sf
    req_power = base_res*speed_mps*sf
    part = classify_parts(req_power, scale)
    req_tq = req_force*part['wheel_r']/wheels
    req_rpm = speed_mps/(2*math.pi*part['wheel_r'])*60
    ideal = part['motor_rpm']/max(req_rpm, 1)
    motor_nm = max(part['motor_nm'], req_tq/(max(ideal, 1)*eff)*1.45)
    center = max(2, round(ideal))
    ratios = []
    for d in range(-2,4):
        r=max(1,center+d)
        if r not in ratios: ratios.append(r)
    for r in [3,4,5,6,8]:
        if len(ratios)>=5: break
        if r not in ratios: ratios.append(r)
    rows=[]
    for r in ratios:
        rpm=part['motor_rpm']/r
        tq=motor_nm*r*eff
        margin=(tq-req_tq)/max(req_tq,0.001)*100
        speed_err=abs(rpm-req_rpm)/max(req_rpm,1)*100
        score=100-speed_err*0.65+min(max(margin,0),120)*0.18
        typ='균형형' if r==center else ('속도형' if r<center else '토크형')
        reason='목표 속도와 요구 토크의 균형이 가장 좋음' if typ=='균형형' else ('휠 RPM이 높아 빠른 주행에 유리하지만 토크 여유는 줄어듦' if typ=='속도형' else '감속비가 커서 등판·하중에 유리하지만 속도는 낮아짐')
        rows.append(dict(ratio=r, rpm=rpm, tq=tq, margin=margin, speed_err=speed_err, score=score, typ=typ, reason=reason, driven=20*r))
    rows=sorted(rows,key=lambda x:x['score'], reverse=True)[:5]
    for i,row in enumerate(rows): row['stars']=5-i
    return part, rows, dict(speed_mps=speed_mps, grade=grade, req_power=req_power, req_tq=req_tq, req_rpm=req_rpm, motor_nm=motor_nm)

def draw_sketch(data, part, best):
    try:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.set_xlim(0, 1100); ax.set_ylim(680,0); ax.axis('off'); ax.set_facecolor('white')
        red, blue = '#d42323', '#174a8b'
        lw=3.5
        ax.plot([230,780,835,185,230],[410,410,500,500,410],color=red,lw=lw)
        ax.plot([310,730,780,250,310],[245,245,410,410,245],color=red,lw=lw)
        ax.plot([360,700],[265,390],color=red,lw=lw); ax.plot([690,365],[265,390],color=red,lw=lw)
        def wheel(x,y,r):
            ax.add_patch(patches.Circle((x,y),r,fill=False,edgecolor=red,lw=lw))
            ax.add_patch(patches.Circle((x,y),r*.45,fill=False,edgecolor=red,lw=2.2))
        if any(k in data['extra'].lower() for k in ['track']) or '궤도' in data['extra'] or '트랙' in data['extra']:
            ax.add_patch(patches.FancyBboxPatch((160,455),720,120,boxstyle='round,pad=0,rounding_size=60',fill=False,edgecolor=red,lw=lw))
            wheel(270,515,48); wheel(760,515,48); wheel(515,525,40)
        else:
            wheel(250,525,55); wheel(780,525,55)
            if data['wheels']>=6: wheel(515,535,45)
        ax.add_patch(patches.Rectangle((200,450),90,40,fill=False,edgecolor=blue,lw=3)); ax.add_patch(patches.Circle((315,470),24,fill=False,edgecolor=blue,lw=3))
        ax.annotate('주행 모터 + 감속기', xy=(235,475), xytext=(55,620), arrowprops=dict(arrowstyle='->',color=blue,lw=2.2), color=blue, fontsize=11, fontweight='bold')
        ax.add_patch(patches.Rectangle((430,430),145,46,fill=False,edgecolor=blue,lw=3)); ax.annotate('배터리/제어기', xy=(500,475), xytext=(440,665), arrowprops=dict(arrowstyle='->',color=blue,lw=2.2), color=blue, fontsize=11, fontweight='bold')
        e=data['extra'].lower()
        if 'intake' in e or '인테이크' in data['extra']:
            ax.add_patch(patches.Rectangle((795,425),110,65,fill=False,edgecolor=red,lw=3)); ax.annotate('intake 흡입부', xy=(850,462), xytext=(850,590), arrowprops=dict(arrowstyle='->',color=blue,lw=2.2), color=blue, fontsize=11, fontweight='bold')
        if 'feeder' in e or '피더' in data['extra']:
            ax.add_patch(patches.Rectangle((330,300),120,60,fill=False,edgecolor=red,lw=3)); ax.annotate('feeder 이송부', xy=(335,325), xytext=(40,305), arrowprops=dict(arrowstyle='->',color=blue,lw=2.2), color=blue, fontsize=11, fontweight='bold')
        if 'shooter' in e or '슈터' in data['extra']:
            ax.add_patch(patches.Rectangle((540,145),155,90,fill=False,edgecolor=red,lw=3)); ax.annotate('shooter 발사 모터', xy=(645,175), xytext=(750,105), arrowprops=dict(arrowstyle='->',color=blue,lw=2.2), color=blue, fontsize=11, fontweight='bold')
        if 'waterwheel' in e or '워터휠' in data['extra']:
            ax.add_patch(patches.Circle((610,335),38,fill=False,edgecolor=red,lw=3)); ax.annotate('waterwheel 색인', xy=(650,335), xytext=(780,325), arrowprops=dict(arrowstyle='->',color=blue,lw=2.2), color=blue, fontsize=11, fontweight='bold')
        ax.text(40,55,'초기 아이디어 스케치',fontsize=16,fontweight='bold')
        ax.text(40,85,data['purpose'][:36],fontsize=12)
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.warning(f'스케치 표시 중 오류 발생: {e}')

# Streamlit 웹 화면 구성
st.title("⚙️ 모빌리티 구동계 설계 최적화 및 성능 예측 시스템 v27")

option_list = ["직접 입력"] + [f"{k}. {v['purpose']} ({v['mass']}kg)" for k, v in PRESETS.items()]
selected_option = st.sidebar.selectbox("프리셋 선택", option_list)

if selected_option != "직접 입력":
    preset_key = int(selected_option.split(".")[0])
    data = PRESETS[preset_key].copy()
else:
    data = dict(
        scale=st.sidebar.selectbox('스케일', ['student', 'research', 'industry']),
        purpose=st.sidebar.text_input('용도', '학생용 이동 로봇'),
        mass=st.sidebar.number_input('질량 (kg)', value=35.0),
        speed=st.sidebar.number_input('속도', value=1.5),
        unit=st.sidebar.selectbox('단위', ['mps', 'kmh']),
        wheels=st.sidebar.number_input('구동 바퀴 수', value=4),
        env=st.sidebar.selectbox('환경', ['indoor', 'normal', 'obstacle', 'extreme']),
        extra=st.sidebar.text_input('기타 요구사항', '없음')
    )

part, rows, calc = analyze(data)

st.subheader("1. 물리 모델 분석 결과")
col1, col2, col3 = st.columns(3)
col1.metric("요구 동력", f"{calc['req_power']:.0f} W")
col2.metric("바퀴당 요구 토크", f"{calc['req_tq']:.2f} Nm")
col3.metric("필요 휠 RPM", f"{calc['req_rpm']:.1f} RPM")
st.info(f"**추천 모터:** {part['motor']} (기준 토크 {calc['motor_nm']:.2f} Nm)")

st.subheader("2. 기어비 후보 분석")
st.table([
    {
        "순위": f"{i}위 ({stars(r['stars'])})",
        "기어비": f"{r['ratio']}:1",
        "치수": f"20T:{r['driven']}T",
        "RPM": f"{r['rpm']:.1f}",
        "토크": f"{r['tq']:.2f} Nm",
        "유형": r['typ'],
        "특징": r['reason']
    } for i, r in enumerate(rows, 1)
])

st.subheader("3. 예산안")
budget = [
    ('주행 구동부', part['motor'], part['motor_cost'], data['wheels']),
    ('주행 구동부', part['gear'], part['gear_cost'], data['wheels']),
    ('바퀴/축/베어링', part['wheel'], part['wheel_cost'], data['wheels']),
    ('제어/전원부', part['control'], part['control_cost'], 1),
    ('주요 구성 형체', part['frame'], part['frame_cost'], 1)
] + aux_items(data['extra'])

total = sum(x[2]*x[3] for x in budget)
st.table([{"분류": cat, "품목": name, "단가": f"{unit:,}원", "수량": qty, "합계": f"{unit*qty:,}원"} for cat, name, unit, qty, *role in budget])
st.success(f"**총 예상 제작 비용: 약 {total:,}원**")

st.subheader("4. 시스템 개념 스케치")
if rows:
    draw_sketch(data, part, rows[0])
