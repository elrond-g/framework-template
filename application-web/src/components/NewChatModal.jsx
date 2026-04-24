import { useEffect, useRef, useState } from "react";

const TAB_PRESET = "preset";
const TAB_CUSTOM = "custom";

const DIRECTION_OPTIONS = ["财运", "事业", "情感", "健康", "学业"];

const INITIAL_FORM = {
  year: "",
  month: "",
  day: "",
  hour: "",
  minute: "",
  gender: "",
  birthplace: "",
  directions: [],
  customDirection: "",
};

function buildPresetPayload(form) {
  const { year, month, day, hour, minute, gender, birthplace, directions, customDirection } = form;
  const allDirections = [...directions];
  if (customDirection.trim()) allDirections.push(customDirection.trim());
  const directionText = allDirections.join("、");
  const prompt =
    `你是一位精通八字的大师，帮我算一下出生于${year}年${month}月${day}日 ${hour}:${minute}的${gender}性，` +
    `出生地是${birthplace}，帮我算一下我的${directionText}。`;
  const formData = { year, month, day, hour, minute, gender, birthplace, directions: allDirections };
  return { kind: "preset", prompt, formData };
}

function isPresetValid(form) {
  const { year, month, day, hour, minute, gender, birthplace, directions, customDirection } = form;
  if (!year || !month || !day || !hour || !minute) return false;
  if (!gender || !birthplace.trim()) return false;
  if (directions.length === 0 && !customDirection.trim()) return false;
  return true;
}

export default function NewChatModal({ onConfirm, onCancel }) {
  const [activeTab, setActiveTab] = useState(TAB_PRESET);
  const [form, setForm] = useState(INITIAL_FORM);
  const [customPrompt, setCustomPrompt] = useState("");
  const firstInputRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (activeTab === TAB_PRESET) {
      firstInputRef.current?.focus();
    } else {
      textareaRef.current?.focus();
    }
  }, [activeTab]);

  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onCancel]);

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const toggleDirection = (dir) => {
    setForm((prev) => {
      const dirs = prev.directions.includes(dir)
        ? prev.directions.filter((d) => d !== dir)
        : [...prev.directions, dir];
      return { ...prev, directions: dirs };
    });
  };

  const presetValid = isPresetValid(form);

  const handleConfirm = () => {
    if (activeTab === TAB_PRESET) {
      if (!presetValid) return;
      onConfirm(buildPresetPayload(form));
    } else {
      onConfirm({ kind: "custom", systemPrompt: customPrompt });
    }
  };

  const handleCustomKeyDown = (e) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleConfirm();
    }
  };

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3 className="modal-title">新建会话</h3>
        <div className="modal-tabs" role="tablist">
          <button
            role="tab"
            aria-selected={activeTab === TAB_PRESET}
            className={`modal-tab${activeTab === TAB_PRESET ? " active" : ""}`}
            onClick={() => setActiveTab(TAB_PRESET)}
          >
            预置提示词
          </button>
          <button
            role="tab"
            aria-selected={activeTab === TAB_CUSTOM}
            className={`modal-tab${activeTab === TAB_CUSTOM ? " active" : ""}`}
            onClick={() => setActiveTab(TAB_CUSTOM)}
          >
            自定义提示词
          </button>
        </div>

        {activeTab === TAB_PRESET ? (
          <>
            <p className="modal-subtitle">填写八字大师表单，创建后直接发起测算</p>
            <div className="bazi-form">
              <div className="bazi-form-row">
                <label className="bazi-label">出生时间</label>
                <div className="bazi-datetime">
                  <input ref={firstInputRef} type="number" placeholder="年" min="1900" max="2100"
                    value={form.year} onChange={(e) => updateField("year", e.target.value)} />
                  <span>年</span>
                  <input type="number" placeholder="月" min="1" max="12"
                    value={form.month} onChange={(e) => updateField("month", e.target.value)} />
                  <span>月</span>
                  <input type="number" placeholder="日" min="1" max="31"
                    value={form.day} onChange={(e) => updateField("day", e.target.value)} />
                  <span>日</span>
                  <input type="number" placeholder="时" min="0" max="23"
                    value={form.hour} onChange={(e) => updateField("hour", e.target.value)} />
                  <span>:</span>
                  <input type="number" placeholder="分" min="0" max="59"
                    value={form.minute} onChange={(e) => updateField("minute", e.target.value)} />
                </div>
              </div>

              <div className="bazi-form-row">
                <label className="bazi-label">性别</label>
                <select value={form.gender} onChange={(e) => updateField("gender", e.target.value)}>
                  <option value="">请选择</option>
                  <option value="男">男</option>
                  <option value="女">女</option>
                </select>
              </div>

              <div className="bazi-form-row">
                <label className="bazi-label">出生地</label>
                <input type="text" placeholder="例如：北京市海淀区"
                  value={form.birthplace} onChange={(e) => updateField("birthplace", e.target.value)} />
              </div>

              <div className="bazi-form-row">
                <label className="bazi-label">测算方向</label>
                <div className="bazi-directions">
                  {DIRECTION_OPTIONS.map((dir) => (
                    <button key={dir} type="button"
                      className={`bazi-dir-btn ${form.directions.includes(dir) ? "active" : ""}`}
                      onClick={() => toggleDirection(dir)}>
                      {dir}
                    </button>
                  ))}
                  <input type="text" className="bazi-custom-dir" placeholder="其他方向"
                    value={form.customDirection} onChange={(e) => updateField("customDirection", e.target.value)} />
                </div>
              </div>
            </div>
          </>
        ) : (
          <>
            <p className="modal-subtitle">
              自定义系统提示词（可选，留空使用默认「八字大师」角色）
            </p>
            <textarea
              ref={textareaRef}
              className="modal-textarea"
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              onKeyDown={handleCustomKeyDown}
              placeholder="例如：你是一位资深旅游顾问，擅长日本关西地区的行程规划……"
              rows={6}
            />
          </>
        )}

        <div className="modal-actions">
          <button className="modal-btn modal-btn-cancel" onClick={onCancel}>
            取消
          </button>
          <button
            className="modal-btn modal-btn-primary"
            onClick={handleConfirm}
            disabled={activeTab === TAB_PRESET && !presetValid}
          >
            创建
          </button>
        </div>
      </div>
    </div>
  );
}
