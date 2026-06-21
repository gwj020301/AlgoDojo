import { beforeEach, describe, expect, it } from 'vitest';

import { clearDraft, loadDraft, loadLanguage, saveDraft, saveLanguage } from './draftStore';

describe('代码自动保存（草稿持久化）', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('全新题目：无草稿时回退到初始模板，且标记为未恢复', () => {
    const res = loadDraft(1, 'python', 'def solve(): pass');
    expect(res.code).toBe('def solve(): pass');
    expect(res.restored).toBe(false);
    expect(res.savedAt).toBeNull();
  });

  it('写到一半 -> 模拟刷新重进 -> 恢复上次内容（而非模板）', () => {
    saveDraft(1, 'python', 'half written code');
    // 模拟刷新后重新进入：传入模板，但应读到草稿
    const res = loadDraft(1, 'python', 'TEMPLATE');
    expect(res.code).toBe('half written code');
    expect(res.restored).toBe(true);
    expect(res.savedAt).not.toBeNull();
  });

  it('Python 与 TypeScript 草稿互不覆盖', () => {
    saveDraft(1, 'python', 'py-code');
    saveDraft(1, 'typescript', 'ts-code');
    expect(loadDraft(1, 'python', 'T').code).toBe('py-code');
    expect(loadDraft(1, 'typescript', 'T').code).toBe('ts-code');
  });

  it('不同题目草稿互相隔离', () => {
    saveDraft(1, 'python', 'problem-1');
    saveDraft(2, 'python', 'problem-2');
    expect(loadDraft(1, 'python', 'T').code).toBe('problem-1');
    expect(loadDraft(2, 'python', 'T').code).toBe('problem-2');
  });

  it('重置：清除草稿后回退模板', () => {
    saveDraft(1, 'python', 'draft');
    clearDraft(1, 'python');
    const res = loadDraft(1, 'python', 'TEMPLATE');
    expect(res.code).toBe('TEMPLATE');
    expect(res.restored).toBe(false);
  });
});

describe('语言选择持久化', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('未保存过：回退到默认语言', () => {
    expect(loadLanguage(1, ['python', 'typescript'], 'python')).toBe('python');
  });

  it('保存 typescript -> 模拟刷新 -> 回到 typescript（不再重置为 python）', () => {
    saveLanguage(1, 'typescript');
    expect(loadLanguage(1, ['python', 'typescript'], 'python')).toBe('typescript');
  });

  it('保存的语言已不在可选列表时回退默认', () => {
    saveLanguage(1, 'rust');
    expect(loadLanguage(1, ['python', 'typescript'], 'python')).toBe('python');
  });
});
