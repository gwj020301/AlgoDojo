// 代码草稿 / 语言选择的本地持久化（自动保存）。
// 抽成纯函数模块，便于单元测试，与 React 组件解耦。

export function draftKey(problemId: number, language: string): string {
  return `algodojo_draft_${problemId}_${language}`;
}

export function draftTimeKey(problemId: number, language: string): string {
  return `${draftKey(problemId, language)}_at`;
}

export function langKey(problemId: number): string {
  return `algodojo_lang_${problemId}`;
}

export interface LoadedDraft {
  code: string;
  /** 是否来自上次保存的草稿（true）而非初始模板（false） */
  restored: boolean;
  /** 上次保存时间（ISO 字符串），无草稿时为 null */
  savedAt: string | null;
}

/** 读取某题某语言的草稿；无草稿则回退到初始模板。 */
export function loadDraft(problemId: number, language: string, template: string): LoadedDraft {
  const draft = localStorage.getItem(draftKey(problemId, language));
  if (draft == null) {
    return { code: template, restored: false, savedAt: null };
  }
  return {
    code: draft,
    restored: true,
    savedAt: localStorage.getItem(draftTimeKey(problemId, language)),
  };
}

/** 保存草稿（自动保存）。返回本次保存时间的 ISO 字符串。 */
export function saveDraft(problemId: number, language: string, code: string): string {
  const iso = new Date().toISOString();
  localStorage.setItem(draftKey(problemId, language), code);
  localStorage.setItem(draftTimeKey(problemId, language), iso);
  return iso;
}

/** 清除草稿（重置为模板时使用）。 */
export function clearDraft(problemId: number, language: string): void {
  localStorage.removeItem(draftKey(problemId, language));
  localStorage.removeItem(draftTimeKey(problemId, language));
}

/** 读取上次选择的语言；无效或缺失则回退到 fallback。 */
export function loadLanguage(problemId: number, languages: string[], fallback: string): string {
  const saved = localStorage.getItem(langKey(problemId));
  return saved && languages.includes(saved) ? saved : fallback;
}

/** 保存当前选择的语言。 */
export function saveLanguage(problemId: number, language: string): void {
  localStorage.setItem(langKey(problemId), language);
}
