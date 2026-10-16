
import os
import json
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, jsonify

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "medical.db"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

SYMPTOMS = {
    "headache": "头痛",
    "dizziness": "头晕",
    "fatigue": "疲劳乏力",
    "fever": "发热",
    "mild_fever": "低热",
    "chills": "发冷或寒战",
    "cough": "咳嗽",
    "sore_throat": "咽痛",
    "runny_nose": "流鼻涕",
    "nasal_congestion": "鼻塞",
    "sneezing": "打喷嚏",
    "itchy_eyes": "眼痒",
    "body_ache": "肌肉酸痛",
    "shortness_of_breath": "呼吸困难或气短",
    "wheezing": "喘鸣",
    "chest_tightness": "胸闷",
    "chest_pain": "胸痛",
    "racing_heart": "心悸或心跳快",
    "nausea": "恶心",
    "vomiting": "呕吐",
    "diarrhea": "腹泻",
    "abdominal_pain": "腹痛",
    "heartburn": "烧心",
    "acid_taste": "反酸或口中酸味",
    "painful_urination": "排尿疼痛",
    "frequent_urination": "尿频",
    "lower_abdominal_pain": "下腹痛",
    "itchy_skin": "皮肤瘙痒",
    "dry_skin": "皮肤干燥",
    "rash": "皮疹",
    "pale_skin": "面色苍白",
    "light_sensitivity": "怕光",
    "sound_sensitivity": "怕声音",
    "sleep_difficulty": "睡眠困难",
    "shortness_of_breath_on_exertion": "活动时气短"
}

SYSTEMS = {
    "头部与神经": [
        "headache", "dizziness", "light_sensitivity",
        "sound_sensitivity", "sleep_difficulty"
    ],
    "呼吸与耳鼻喉": [
        "cough", "sore_throat", "runny_nose",
        "nasal_congestion", "sneezing", "wheezing",
        "shortness_of_breath"
    ],
    "心血管与胸部": [
        "chest_pain", "chest_tightness", "racing_heart",
        "shortness_of_breath_on_exertion"
    ],
    "全身症状": [
        "fever", "mild_fever", "chills", "fatigue",
        "body_ache", "pale_skin"
    ],
    "消化系统": [
        "nausea", "vomiting", "diarrhea",
        "abdominal_pain", "heartburn", "acid_taste"
    ],
    "泌尿系统": [
        "painful_urination", "frequent_urination",
        "lower_abdominal_pain"
    ],
    "皮肤与过敏": [
        "itchy_skin", "dry_skin", "rash", "itchy_eyes"
    ]
}

RED_FLAGS = {
    "severe_chest_pain": "新发或严重胸痛",
    "severe_breathing": "明显或迅速加重的呼吸困难",
    "fainting": "晕厥或意识丧失",
    "confusion": "突然意识混乱或难以唤醒",
    "stroke_signs": "突然出现面部歪斜、单侧无力或说话困难",
    "severe_bleeding": "大量出血或呕血"
}

DISEASES = [
    {
        "id": "common_cold",
        "name": "普通感冒",
        "category": "呼吸系统",
        "symptoms": [
            "runny_nose", "sore_throat", "cough",
            "sneezing", "mild_fever", "nasal_congestion"
        ],
        "causes": "通常由呼吸道病毒引起，可通过呼吸道飞沫、气溶胶及接触传播。",
        "symptom_detail": "常见表现为流鼻涕、鼻塞、打喷嚏、咽痛和咳嗽，有时伴低热。",
        "tests": "典型轻症通常根据病史和体格检查评估。必要时医生会考虑其他呼吸道感染。",
        "treatment": "多数病例可以自行缓解。休息、补水，并咨询药师选择适合年龄和健康情况的对症措施。抗生素不能治疗病毒性感冒。",
        "sources": [
            ["CDC：普通感冒", "https://www.cdc.gov/common-cold/about/index.html"]
        ]
    },
    {
        "id": "influenza",
        "name": "流感",
        "category": "呼吸系统",
        "symptoms": [
            "fever", "mild_fever", "cough", "sore_throat",
            "body_ache", "fatigue", "headache", "chills"
        ],
        "causes": "由流感病毒感染引起，通过呼吸道传播。",
        "symptom_detail": "可能突然发热、发冷、肌肉酸痛、头痛、咳嗽和明显疲劳，并非每个人都会发热。",
        "tests": "医生会结合症状、流行情况和个人风险判断，必要时进行流感检测。",
        "treatment": "休息、补液。部分患者可能适合抗病毒处方药，尤其是重症或高风险人群，应尽早咨询医生。",
        "sources": [
            ["加拿大政府：流感", "https://www.canada.ca/en/public-health/services/diseases/flu-influenza.html"],
            ["CDC：流感治疗", "https://www.cdc.gov/flu/treatment/index.html"]
        ]
    },
    {
        "id": "allergic_rhinitis",
        "name": "过敏性鼻炎",
        "category": "免疫与耳鼻喉",
        "symptoms": [
            "runny_nose", "sneezing", "itchy_eyes",
            "nasal_congestion"
        ],
        "causes": "免疫系统对花粉、尘螨、宠物皮屑或霉菌等过敏原产生反应。",
        "symptom_detail": "常见表现为连续打喷嚏、清水样鼻涕、鼻痒、鼻塞和眼痒。",
        "tests": "通常根据病史判断；必要时由医生安排过敏原检查。",
        "treatment": "尽量减少接触过敏原。生理盐水、部分抗组胺药或鼻用药物可能有帮助，应根据年龄和健康情况咨询医生或药师。",
        "sources": [
            ["NHS：过敏性鼻炎", "https://www.nhs.uk/conditions/allergic-rhinitis/"]
        ]
    },
    {
        "id": "migraine",
        "name": "偏头痛",
        "category": "神经系统",
        "symptoms": [
            "headache", "nausea", "light_sensitivity",
            "sound_sensitivity"
        ],
        "causes": "与神经系统活动及遗传易感性等因素有关。睡眠变化、压力和脱水等可能成为个体诱因。",
        "symptom_detail": "可能出现反复头痛、恶心、怕光或怕声音；部分患者出现先兆。",
        "tests": "通常根据病史和神经系统检查评估。突然发生的剧烈头痛或伴神经功能异常需要紧急排查其他病因。",
        "treatment": "规律睡眠、补水并记录头痛情况。急性治疗和预防治疗需要医生根据具体情况选择。",
        "sources": [
            ["NHS：偏头痛", "https://www.nhs.uk/conditions/migraine/"]
        ]
    },
    {
        "id": "gastroenteritis",
        "name": "急性胃肠炎",
        "category": "消化系统",
        "symptoms": [
            "diarrhea", "vomiting", "nausea",
            "abdominal_pain", "mild_fever"
        ],
        "causes": "可能由病毒、细菌、寄生虫或受污染的食物和水引起。",
        "symptom_detail": "可能出现腹泻、恶心、呕吐、腹部绞痛，有时伴发热。",
        "tests": "轻症通常不需要特殊检查；血便、严重脱水或持续症状可能需要医学评估。",
        "treatment": "重点是补液，可在专业指导下使用口服补液盐。严重脱水、血便或持续呕吐时应及时就医。不要自行使用抗生素。",
        "sources": [
            ["NHS：腹泻和呕吐", "https://www.nhs.uk/conditions/diarrhoea-and-vomiting/"]
        ]
    },
    {
        "id": "gerd",
        "name": "胃食管反流病",
        "category": "消化系统",
        "symptoms": ["heartburn", "acid_taste"],
        "causes": "胃内容物反流进入食管，可能与食管下括约肌功能及其他因素有关。",
        "symptom_detail": "可能出现胸口烧灼感、酸水上涌或口中酸味。胸部不适也可能由其他疾病造成。",
        "tests": "医生会结合症状和危险信号评估；持续、难治或伴吞咽困难时可能需要进一步检查。",
        "treatment": "可避免个人明确的诱发因素，并避免睡前大量进食。药物需结合年龄、症状和禁忌证咨询医生或药师。",
        "sources": [
            ["NIDDK：胃食管反流", "https://www.niddk.nih.gov/health-information/digestive-diseases/acid-reflux-ger-gerd-adults"]
        ]
    },
    {
        "id": "uti",
        "name": "尿路感染",
        "category": "泌尿系统",
        "symptoms": [
            "painful_urination", "frequent_urination",
            "lower_abdominal_pain"
        ],
        "causes": "多数由细菌进入尿路并繁殖引起。",
        "symptom_detail": "可能出现排尿疼痛、尿频、尿急或下腹不适。发热、腰背侧痛或呕吐可能提示更严重感染。",
        "tests": "医生可能进行尿液检查，必要时进行尿培养。",
        "treatment": "由医务人员判断是否需要抗生素并选择方案。不要使用剩余抗生素或与他人共用药物。",
        "sources": [
            ["NHS：尿路感染", "https://www.nhs.uk/conditions/urinary-tract-infections-utis/"]
        ]
    },
    {
        "id": "eczema",
        "name": "湿疹 / 特应性皮炎",
        "category": "皮肤",
        "symptoms": ["itchy_skin", "dry_skin", "rash"],
        "causes": "与皮肤屏障功能、免疫反应和遗传因素有关；干燥和刺激物可能加重症状。",
        "symptom_detail": "常见皮肤干燥、瘙痒、红疹或反复发作；其他皮肤病也可能有类似表现。",
        "tests": "通常由医生根据皮肤表现和病史判断；不典型或疑似感染时需要进一步评估。",
        "treatment": "温和清洁、使用无香保湿剂并避免已知刺激物。外用药的种类和强度应由专业人员指导。",
        "sources": [
            ["NHS：特应性湿疹", "https://www.nhs.uk/conditions/atopic-eczema/"]
        ]
    },
    {
        "id": "anemia",
        "name": "贫血（多种原因）",
        "category": "血液系统",
        "symptoms": [
            "fatigue", "dizziness", "shortness_of_breath_on_exertion",
            "pale_skin", "headache"
        ],
        "causes": "原因包括缺铁、维生素缺乏、慢性疾病、遗传性血液疾病或失血等。",
        "symptom_detail": "可能出现疲劳、头晕、面色苍白、头痛或活动时气短。",
        "tests": "通常需要血常规；医生可能进一步检查铁蛋白、维生素水平或其他指标。",
        "treatment": "治疗取决于具体原因。不要仅凭疲劳自行长期补铁，应先接受适当评估。",
        "sources": [
            ["NHLBI：贫血", "https://www.nhlbi.nih.gov/health/anemia"]
        ]
    },
    {
        "id": "asthma",
        "name": "哮喘（可能性之一）",
        "category": "呼吸系统",
        "symptoms": [
            "wheezing", "cough", "shortness_of_breath",
            "chest_tightness"
        ],
        "causes": "气道慢性炎症和高反应性可能导致气道变窄；运动、冷空气、烟雾或感染可能诱发症状。",
        "symptom_detail": "可能出现反复喘鸣、咳嗽、胸闷或呼吸困难。呼吸困难也可能来自其他急症。",
        "tests": "医生可能安排肺功能检查，并结合病史和体格检查评估。",
        "treatment": "需要医生制定个体化管理计划，吸入药物及其用法应由专业人员指导。严重呼吸困难应立即呼叫急救。",
        "sources": [
            ["GINA：全球哮喘管理策略", "https://ginasthma.org/"],
            ["加拿大政府：哮喘", "https://www.canada.ca/en/public-health/services/chronic-diseases/chronic-respiratory-diseases/asthma.html"]
        ]
    },
    {
        "id": "anxiety",
        "name": "焦虑相关症状（需排除身体原因）",
        "category": "心理健康",
        "symptoms": [
            "racing_heart", "shortness_of_breath",
            "dizziness", "nausea", "sleep_difficulty"
        ],
        "causes": "可能涉及压力反应、心理因素和生物学因素。心悸、气短和头晕也可能存在身体原因。",
        "symptom_detail": "可能出现紧张、担忧、心跳加快、头晕、胃部不适或睡眠困难，不能仅凭这些症状确诊。",
        "tests": "由合格专业人员进行评估；首次或严重的心悸、胸痛、晕厥或气短应先排查身体原因。",
        "treatment": "心理治疗、压力管理和规律作息可能有帮助。是否需要药物应由临床专业人员评估。",
        "sources": [
            ["NHS：广泛性焦虑障碍", "https://www.nhs.uk/mental-health/conditions/generalised-anxiety-disorder/overview/"]
        ]
    }
]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS diseases (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                symptoms TEXT NOT NULL,
                causes TEXT NOT NULL,
                symptom_detail TEXT NOT NULL,
                tests TEXT NOT NULL,
                treatment TEXT NOT NULL,
                sources TEXT NOT NULL
            )
        """)
        for disease in DISEASES:
            conn.execute("""
                INSERT OR REPLACE INTO diseases
                (id, name, category, symptoms, causes,
                 symptom_detail, tests, treatment, sources)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                disease["id"], disease["name"], disease["category"],
                json.dumps(disease["symptoms"], ensure_ascii=False),
                disease["causes"], disease["symptom_detail"],
                disease["tests"], disease["treatment"],
                json.dumps(disease["sources"], ensure_ascii=False)
            ))


def label_for(code):
    return SYMPTOMS.get(code, code)


@app.route("/")
def index():
    return render_template(
        "index.html",
        systems=SYSTEMS,
        symptoms=SYMPTOMS,
        red_flags=RED_FLAGS
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}

    try:
        age = int(data.get("age", -1))
    except (TypeError, ValueError):
        return jsonify({"error": "请输入有效年龄。"}), 400

    if not 0 <= age <= 120:
        return jsonify({"error": "年龄必须在 0 到 120 岁之间。"}), 400

    sex = str(data.get("sex", "unspecified"))
    duration = str(data.get("duration", "unknown"))[:40]
    selected = data.get("symptoms", [])
    selected_flags = data.get("red_flags", [])

    if not isinstance(selected, list) or not isinstance(selected_flags, list):
        return jsonify({"error": "提交的数据格式不正确。"}), 400

    valid_symptoms = set(SYMPTOMS)
    selected = list(dict.fromkeys(
        x for x in selected if isinstance(x, str) and x in valid_symptoms
    ))
    selected_flags = list(dict.fromkeys(
        x for x in selected_flags
        if isinstance(x, str) and x in RED_FLAGS
    ))

    if not selected:
        return jsonify({"error": "请至少选择一个症状。"}), 400

    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM diseases").fetchall()

    chosen = set(selected)
    results = []

    for row in rows:
        disease_symptoms = set(json.loads(row["symptoms"]))
        matched = chosen.intersection(disease_symptoms)

        if not matched:
            continue

        # 这是简单的展示排序分数，不是患病概率。
        coverage = len(matched) / max(1, len(chosen))
        symptom_ratio = len(matched) / max(1, len(disease_symptoms))
        score = round(100 * (0.65 * coverage + 0.35 * symptom_ratio))

        results.append({
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "score": score,
            "matched": [label_for(x) for x in sorted(matched)],
            "causes": row["causes"],
            "symptom_detail": row["symptom_detail"],
            "tests": row["tests"],
            "treatment": row["treatment"],
            "sources": json.loads(row["sources"])
        })

    results.sort(key=lambda item: item["score"], reverse=True)

    return jsonify({
        "age": age,
        "sex": sex,
        "duration": duration,
        "selected_symptoms": [label_for(x) for x in selected],
        "red_flags": [
            {"code": code, "label": RED_FLAGS[code]}
            for code in selected_flags
        ],
        "emergency_warning": bool(selected_flags),
        "results": results[:10],
        "disclaimer": (
            "这是教育用途的示例工具，不是诊断系统。疾病库不完整，"
            "排序分数不是患病概率，未经过临床验证。"
        )
    })


# 在本地和云端启动时初始化示例数据库。
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)

