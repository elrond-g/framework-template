import { useState } from "react";

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

function MessageInput({ onSend, disabled }) {
  const [form, setForm] = useState(INITIAL_FORM);

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

  const isValid = () => {
    const { year, month, day, hour, minute, gender, birthplace, directions, customDirection } = form;
    if (!year || !month || !day || !hour || !minute) return false;
    if (!gender || !birthplace.trim()) return false;
    if (directions.length === 0 && !customDirection.trim()) return false;
    return true;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isValid() || disabled) return;

    const { year, month, day, hour, minute, gender, birthplace, directions, customDirection } = form;
    const allDirections = [...directions];
    if (customDirection.trim()) {
      allDirections.push(customDirection.trim());
    }
    const directionText = allDirections.join("、");

    const prompt =
      `你是一位精通八字的大师，帮我算一下出生于${year}年${month}月${day}日 ${hour}:${minute}的${gender}性，` +
      `出生地是${birthplace}，帮我算一下我的${directionText}。`;

    onSend(prompt);
    setForm(INITIAL_FORM);
  };

  return (
    <div className="message-input-wrapper">
      <form className="bazi-form" onSubmit={handleSubmit}>
        <div className="bazi-form-row">
          <label className="bazi-label">出生时间</label>
          <div className="bazi-datetime">
            <input type="number" placeholder="年" min="1900" max="2100"
              value={form.year} onChange={(e) => updateField("year", e.target.value)} disabled={disabled} />
            <span>年</span>
            <input type="number" placeholder="月" min="1" max="12"
              value={form.month} onChange={(e) => updateField("month", e.target.value)} disabled={disabled} />
            <span>月</span>
            <input type="number" placeholder="日" min="1" max="31"
              value={form.day} onChange={(e) => updateField("day", e.target.value)} disabled={disabled} />
            <span>日</span>
            <input type="number" placeholder="时" min="0" max="23"
              value={form.hour} onChange={(e) => updateField("hour", e.target.value)} disabled={disabled} />
            <span>:</span>
            <input type="number" placeholder="分" min="0" max="59"
              value={form.minute} onChange={(e) => updateField("minute", e.target.value)} disabled={disabled} />
          </div>
        </div>

        <div className="bazi-form-row">
          <label className="bazi-label">性别</label>
          <select value={form.gender} onChange={(e) => updateField("gender", e.target.value)} disabled={disabled}>
            <option value="">请选择</option>
            <option value="男">男</option>
            <option value="女">女</option>
          </select>
        </div>

        <div className="bazi-form-row">
          <label className="bazi-label">出生地</label>
          <input type="text" placeholder="例如：北京市海淀区"
            value={form.birthplace} onChange={(e) => updateField("birthplace", e.target.value)} disabled={disabled} />
        </div>

        <div className="bazi-form-row">
          <label className="bazi-label">测算方向</label>
          <div className="bazi-directions">
            {DIRECTION_OPTIONS.map((dir) => (
              <button key={dir} type="button"
                className={`bazi-dir-btn ${form.directions.includes(dir) ? "active" : ""}`}
                onClick={() => toggleDirection(dir)} disabled={disabled}>
                {dir}
              </button>
            ))}
            <input type="text" className="bazi-custom-dir" placeholder="其他方向"
              value={form.customDirection} onChange={(e) => updateField("customDirection", e.target.value)} disabled={disabled} />
          </div>
        </div>

        <button type="submit" className="bazi-submit" disabled={disabled || !isValid()}>
          开始测算
        </button>
      </form>
    </div>
  );
}

export default MessageInput;
