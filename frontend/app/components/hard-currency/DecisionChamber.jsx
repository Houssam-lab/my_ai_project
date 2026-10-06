"use client";

/**
 * «غرفة القرار» (D-314) — للمدير وحده، وأوّل ما يراه في المركز.
 *
 * لا تبدأ بـ«كيف أساعدك؟»: تبدأ بما يسمح الواقع بقوله، وما لم يقله بعد، وأصغر فعلٍ بشريٍّ
 * يغيّره. أربعة أبواب لا محادثةٌ حرّة. وكلّ جملةٍ تحمل صنفها نصّاً (لا لوناً وحده) ودليلها.
 * ⛔ لا شيء هنا يكتب: باب «سجّل نتيجة» يعاين السطر، والمالك يلتزمه عبر git.
 */

import React, { useId, useState } from 'react';
import styles from './HardCurrencyCenter.module.css';
import { StatusPanel, EmptyState } from './StatusPanel';
import { useHardCurrencyAction } from '../../hooks/useHardCurrencyApi';

const CLASS_LABELS = {
    FACT: 'حقيقة',
    HYPOTHESIS: 'فرضية',
    UNKNOWN: 'مجهول',
    ACTION: 'فعل',
    REFUSAL: 'رفض',
};
const STATUS_LABELS = {
    SUPPORTED: 'مسنود',
    NOT_SUPPORTED: 'غير مسنود',
    UNKNOWN: 'مجهول',
};
const QUESTION_LABELS = {
    ready: 'هل نحن جاهزون؟ — لماذا بالضبط؟',
    build: 'ماذا نبني؟ — هل الكود هو الاختناق؟',
    why_no_money: 'لماذا لا مال بعد؟ — أين تنقطع السلسلة؟',
    say_to_buyer: 'هل يجوز قول هذه الجملة لمشترٍ؟',
};
const DOORS = [
    { id: 'evidence', label: 'افحص الأدلّة' },
    { id: 'challenge', label: 'اطعن في الاستنتاج' },
    { id: 'prepare', label: 'حضّر الفعل البشري التالي' },
    { id: 'record', label: 'سجّل نتيجةً مؤكَّدة' },
];
const MAX_TEXT = 2000;

function ClassChip({ cls }) {
    return <span className={`${styles.badge} ${styles[`chip_${cls}`] ?? ''}`}>{CLASS_LABELS[cls] ?? cls}</span>;
}

function SentenceList({ sentences }) {
    if (!sentences?.length) return <EmptyState>لا جمل.</EmptyState>;
    return (
        <ul className={styles.sentenceList}>
            {sentences.map((item, index) => (
                <li key={`${index}-${item.sentence}`} className={styles.sentence}>
                    <ClassChip cls={item.class} />
                    <span>{item.sentence}</span>
                    {item.evidence_ids?.map((id) => (
                        <code key={id} className={styles.evidence}>
                            {id}
                        </code>
                    ))}
                </li>
            ))}
        </ul>
    );
}

function Item({ label, primary, children }) {
    return (
        <li className={primary ? `${styles.chamberItem} ${styles.chamberItemPrimary}` : styles.chamberItem}>
            <span className={styles.chamberLabel}>{label}</span>
            <div className={styles.chamberValue}>{children}</div>
        </li>
    );
}

/** الشاشة الأولى: تسعة أسطر لا أكثر — ما يسمح به الواقع وما يرفض قوله وأصغر فعلٍ يغيّره. */
function FirstScreen({ snapshot, brief }) {
    const ceiling = snapshot.ceiling ?? {};
    const missing = snapshot.first_missing_proof;
    const action = brief.primary_action;
    const kill = brief.capsule?.kill_condition ?? snapshot.kill_conditions?.find((k) => k.kill_id === 'K1');
    const last = snapshot.last_event;
    return (
        <ol className={styles.chamberList}>
            <Item label="1 · الأطروحة النشطة الوحيدة">
                <code className={styles.evidence}>{snapshot.thesis?.id}</code> ({snapshot.thesis?.decision}) · حالة الكتالوج:{' '}
                {snapshot.thesis?.catalog_status ?? '—'}
            </Item>
            <Item label="2 · أقصى ادّعاءٍ صادقٍ مسموح">
                {ceiling.statement_ar} <span className={styles.muted}>— الحلقة {ceiling.link} من 8</span>
            </Item>
            <Item label="3 · أوّل دليلٍ ناقص">
                {missing ? (
                    <>
                        الحلقة {missing.link}: {missing.title_ar}
                        {missing.reason_ar && <div className={styles.muted}>{missing.reason_ar}</div>}
                    </>
                ) : (
                    'لا دليل ناقص في السلسلة'
                )}
            </Item>
            <Item label="4 · لماذا لا يولّده الكود">{missing?.why_not_code_ar ?? '—'}</Item>
            <Item label="5 · الفعل البشري التالي" primary>
                {action ? (
                    <strong>{action.title_ar}</strong>
                ) : (
                    <>
                        <strong>لا قرار قانونيٌّ متاح.</strong> {brief.reason_ar}
                        {brief.details?.length > 0 && (
                            <ul className={styles.plainList}>
                                {brief.details.map((line) => (
                                    <li key={line}>{line}</li>
                                ))}
                            </ul>
                        )}
                    </>
                )}
            </Item>
            <Item label="6 · الدليل الذي قد يُنتجه">
                {action?.produces?.length ? action.produces.join(' · ') : '—'}
            </Item>
            <Item label="7 · الشرط الذي يقتل الأطروحة">
                {kill ? (
                    <>
                        «{kill.source_quote}» — {kill.status}
                        <div className={styles.muted}>{kill.progress}</div>
                    </>
                ) : (
                    '—'
                )}
            </Item>
            <Item label="8 · الاختصار الممنوع الأكثر إغراءً الآن">{brief.tempting_shortcut_ar}</Item>
            <Item label="9 · منذ آخر حدثٍ اقتصاديٍّ موثّق">
                {last ? (
                    <>
                        {snapshot.days_since_last_event} يوماً — {last.action} لـ{last.entity} في {last.date}
                    </>
                ) : (
                    'لا حدث في السجلّ'
                )}
            </Item>
        </ol>
    );
}

function EvidenceDoor({ snapshot, sentences }) {
    return (
        <div>
            <h4 className={styles.subhead}>جمل الغرفة وأدلّتها</h4>
            <SentenceList sentences={sentences} />
            <h4 className={styles.subhead}>التناقضات ({snapshot.contradictions?.length ?? 0})</h4>
            {snapshot.contradictions?.length ? (
                <ul className={styles.plainList}>
                    {snapshot.contradictions.map((item) => (
                        <li key={item.detail_ar}>
                            <span className={styles.warning}>{item.kind}</span> — {item.detail_ar}
                        </li>
                    ))}
                </ul>
            ) : (
                <EmptyState>لا تناقض مرصود بهذه الفحوص.</EmptyState>
            )}
            <h4 className={styles.subhead}>ما لا يراه النظام ({snapshot.blind_spots?.length ?? 0})</h4>
            <ul className={styles.plainList}>
                {(snapshot.blind_spots ?? []).map((item) => (
                    <li key={item.detail_ar}>{item.detail_ar}</li>
                ))}
            </ul>
            <div className={styles.tableWrap}>
                <table className={styles.table}>
                    <caption className={styles.muted}>الادّعاءات: ما يتطلّبه كلٌّ، ومن يملك دليله، وما يُغري باختصاره</caption>
                    <thead>
                        <tr>
                            <th scope="col">الادّعاء</th>
                            <th scope="col">الحالة</th>
                            <th scope="col">يتطلّب</th>
                            <th scope="col">الفاعل الخارجي</th>
                            <th scope="col">الاختصار الممنوع</th>
                        </tr>
                    </thead>
                    <tbody>
                        {(snapshot.claims ?? []).map((claim) => (
                            <tr key={claim.claim_id}>
                                <td>{claim.statement_ar}</td>
                                <td>{STATUS_LABELS[claim.status] ?? claim.status}</td>
                                <td>{claim.requires_ar}</td>
                                <td>{claim.external_actor_ar}</td>
                                <td>{claim.forbidden_shortcut_ar}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <div className={styles.tableWrap}>
                <table className={styles.table}>
                    <caption className={styles.muted}>سجلّ الأدلّة: ما يُثبته كلُّ دليل وما لا يستطيع إثباته</caption>
                    <thead>
                        <tr>
                            <th scope="col">المعرّف</th>
                            <th scope="col">يُثبت</th>
                            <th scope="col">لا يُثبت</th>
                            <th scope="col">على القرص</th>
                        </tr>
                    </thead>
                    <tbody>
                        {(snapshot.evidence ?? []).map((item) => (
                            <tr key={item.id}>
                                <td dir="ltr">{item.id}</td>
                                <td>{item.proves_ar}</td>
                                <td>{item.cannot_prove_ar}</td>
                                <td>{item.exists ? 'نعم' : 'لا'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function ChallengeDoor({ token, questions }) {
    const [question, setQuestion] = useState(questions[0] ?? 'ready');
    const [text, setText] = useState('');
    const action = useHardCurrencyAction(token);
    const textId = useId();

    const submit = (event) => {
        event.preventDefault();
        const json = question === 'say_to_buyer' ? { question, text } : { question };
        action.run('/chamber/cross-examination', { method: 'POST', json });
    };

    return (
        <div>
            <form className={styles.form} onSubmit={submit}>
                <fieldset className={styles.fieldsetStacked}>
                    <legend>السؤال (مجموعةٌ مغلقة — لا محادثة حرّة)</legend>
                    {questions.map((id) => (
                        <label key={id}>
                            <input
                                type="radio"
                                name="chamber-question"
                                value={id}
                                checked={question === id}
                                onChange={() => setQuestion(id)}
                            />{' '}
                            {QUESTION_LABELS[id] ?? id}
                        </label>
                    ))}
                </fieldset>
                {question === 'say_to_buyer' && (
                    <div className={styles.field}>
                        <label htmlFor={textId}>الجملة كما ستُرسَل (حتى {MAX_TEXT} حرف)</label>
                        <textarea
                            id={textId}
                            rows={3}
                            maxLength={MAX_TEXT}
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            dir="auto"
                        />
                    </div>
                )}
                <button
                    type="submit"
                    className={styles.button}
                    disabled={action.state === 'loading' || (question === 'say_to_buyer' && !text.trim())}
                >
                    {action.state === 'loading' ? 'جارٍ الاستجواب…' : 'استجوب'}
                </button>
            </form>
            <StatusPanel state={action.state} message={action.message} slow={action.slow} onCancel={action.cancel} />
            {action.state === 'success' && action.data && (
                <div className={styles.result} aria-live="polite">
                    {action.data.verdict && (
                        <p>
                            الحكم: <strong>{action.data.verdict}</strong>
                        </p>
                    )}
                    <SentenceList sentences={action.data.sentences} />
                </div>
            )}
        </div>
    );
}

function PrepareDoor({ brief }) {
    const capsule = brief.capsule;
    const action = brief.primary_action;
    const template = brief.ledger_row_template;
    if (!action || !capsule) {
        return <EmptyState>لا فعل يُحضَّر: {brief.reason_ar}</EmptyState>;
    }
    const rows = [
        ['الفرضية', capsule.claim_ar],
        ['الآلية', capsule.mechanism_ar],
        ['أصغر اختبارٍ يُسقطها', capsule.minimum_falsification_test_ar],
        ['المالك', capsule.human_owner_ar],
        ['السقف الزمني', capsule.max_time_ar],
        ['السقف المالي', capsule.max_cost_ar],
        ['الخطر', capsule.risk_ar],
        ['ما يتغيّر في القرار', capsule.expected_decision_change_ar],
        ['ملاحظة النجاح', capsule.success_observation_ar],
        ['ملاحظة الفشل', capsule.failure_observation_ar],
        ['الصلاحية', capsule.expiry_ar],
    ];
    return (
        <div>
            <p>
                <strong>{action.title_ar}</strong> <span className={styles.badgeMuted}>{capsule.status}</span>
            </p>
            <ol className={styles.linkList}>
                {action.steps_ar.map((step) => (
                    <li key={step} className={styles.linkRow}>
                        {step}
                    </li>
                ))}
            </ol>
            <dl className={styles.capsule}>
                {rows.map(([label, value]) => (
                    <div key={label}>
                        <dt>{label}</dt>
                        <dd>{value}</dd>
                    </div>
                ))}
            </dl>
            {template && (
                <>
                    <h4 className={styles.subhead}>السطر الذي يُسجَّل بعد الفعل (قالب)</h4>
                    <code className={styles.csvLine}>{Object.values(template).join(',')}</code>
                </>
            )}
            <h4 className={styles.subhead}>لماذا هذا الفعل لا غيره</h4>
            <p className={styles.muted}>{brief.selection_rule_ar}</p>
            <ul className={styles.plainList}>
                {brief.candidates_considered.map((c) => (
                    <li key={c.action_id}>
                        {c.chosen ? '✓' : '○'} {c.action_id} — قانونيٌّ الآن: {c.lawful_now ? 'نعم' : 'لا'} · قابلٌ للتراجع:{' '}
                        {c.reversible ? 'نعم' : 'لا'} · رتبة الوقت: {c.time_rank}
                        {c.requires_supported?.length > 0 && ` · يتطلّب: ${c.requires_supported.join('، ')}`}
                    </li>
                ))}
            </ul>
        </div>
    );
}

const FIELDS = [
    ['date', 'التاريخ (YYYY-MM-DD)', 'ltr'],
    ['target_ref', 'مرجع الهدف', 'ltr'],
    ['entity', 'الكيان', 'auto'],
    ['country', 'البلد (ISO)', 'ltr'],
    ['amount_eur', 'المبلغ € (للمال وعرض السعر فقط)', 'ltr'],
    ['evidence_ref', 'مرجع الدليل (كشف بنكي · إيصال)', 'ltr'],
    ['note', 'ملاحظة', 'auto'],
];

function todayIso() {
    const now = new Date();
    const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 10);
}

function initialRow(template) {
    const base = template ?? {};
    const clean = (value) => (typeof value === 'string' && value.startsWith('<') ? '' : value ?? '');
    return {
        date: todayIso(),
        target_ref: clean(base.target_ref),
        entity: clean(base.entity),
        country: clean(base.country) || 'FR',
        channel: base.channel || 'email',
        action: base.action || 'EMAIL_SENT',
        amount_eur: clean(base.amount_eur),
        evidence_ref: clean(base.evidence_ref),
        note: '',
    };
}

function RecordDoor({ token, brief, vocabulary }) {
    const [row, setRow] = useState(() => initialRow(brief.ledger_row_template));
    const [copied, setCopied] = useState('');
    const action = useHardCurrencyAction(token);
    const formId = useId();
    const set = (key) => (event) => setRow((current) => ({ ...current, [key]: event.target.value }));

    const submit = (event) => {
        event.preventDefault();
        setCopied('');
        action.run('/chamber/outcome-preview', { method: 'POST', json: row });
    };
    const copy = async (line) => {
        try {
            await navigator.clipboard.writeText(line);
            setCopied('نُسخ السطر.');
        } catch {
            setCopied('تعذّر النسخ — حدّد السطر وانسخه يدوياً.');
        }
    };
    const result = action.state === 'success' ? action.data : null;

    return (
        <div>
            <p className={styles.truthBanner} role="note">
                هذا الباب لا يكتب شيئاً. يتحقّق من الصفّ (القواعد · الانتقالات · التوجيه) ويعرض السطر وما يتغيّر — ثمّ تلتزمه
                أنت عبر git، والالتزام هو سجلّ التدقيق.
            </p>
            <form className={styles.form} onSubmit={submit}>
                <div className={styles.formGrid}>
                    {FIELDS.map(([key, label, dir]) => (
                        <div key={key} className={styles.field}>
                            <label htmlFor={`${formId}-${key}`}>{label}</label>
                            <input id={`${formId}-${key}`} value={row[key]} onChange={set(key)} dir={dir} />
                        </div>
                    ))}
                    <div className={styles.field}>
                        <label htmlFor={`${formId}-channel`}>القناة</label>
                        <select id={`${formId}-channel`} value={row.channel} onChange={set('channel')}>
                            {(vocabulary?.channels ?? []).map((name) => (
                                <option key={name} value={name}>
                                    {name}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className={styles.field}>
                        <label htmlFor={`${formId}-action`}>الفعل</label>
                        <select id={`${formId}-action`} value={row.action} onChange={set('action')}>
                            {(vocabulary?.actions ?? []).map((name) => (
                                <option key={name} value={name}>
                                    {name}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
                <button type="submit" className={styles.button} disabled={action.state === 'loading'}>
                    {action.state === 'loading' ? 'جارٍ التحقّق…' : 'عاين الصفّ'}
                </button>
            </form>
            <StatusPanel state={action.state} message={action.message} slow={action.slow} onCancel={action.cancel} />
            {result && (
                <div className={styles.result} aria-live="polite">
                    {result.accepted ? (
                        <p className={styles.ok}>مقبول — لم يُكتب شيء (written = {String(result.written)}).</p>
                    ) : (
                        <div className={styles.statusError} role="alert">
                            <strong>مرفوض: هذا الصفّ يُحمِّر البوّابة.</strong>
                            <ul className={styles.plainList}>
                                {result.problems.map((problem) => (
                                    <li key={problem}>{problem}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                    <code className={styles.csvLine}>{result.csv_line}</code>
                    {result.accepted && (
                        <>
                            <div className={styles.actions}>
                                <button type="button" className={styles.buttonSecondary} onClick={() => copy(result.csv_line)}>
                                    انسخ السطر
                                </button>
                                {copied && <span className={styles.muted}>{copied}</span>}
                            </div>
                            <p className={styles.muted}>{result.commit_hint_ar}</p>
                            {result.delta && (
                                <ul className={styles.plainList}>
                                    <li>
                                        السقف: الحلقة {result.delta.ceiling[0]} ← {result.delta.ceiling[1]}
                                    </li>
                                    <li>
                                        الفعل التالي: {result.delta.primary_action[0] ?? '—'} ← {result.delta.primary_action[1] ?? '—'}
                                    </li>
                                    <li>
                                        شروط القتل: {result.delta.kill_conditions[0].join(' · ')} ←{' '}
                                        {result.delta.kill_conditions[1].join(' · ')}
                                    </li>
                                </ul>
                            )}
                        </>
                    )}
                </div>
            )}
        </div>
    );
}

export function DecisionChamber({ token, data }) {
    const [door, setDoor] = useState('evidence');
    const { snapshot, brief, sentences, questions, ledger_vocabulary: vocabulary } = data;
    return (
        <section aria-labelledby="chamber-title">
            <h3 id="chamber-title" className={styles.sectionTitle}>غرفة القرار</h3>
            <p className={styles.truthBanner} role="note">
                هذا ما يسمح الواقع بقوله. وهذا ما لم يقله بعد. وهذا أصغر فعلٍ بشريٍّ يمكن أن يغيّره — الآلة لا تنفّذه.
            </p>
            <FirstScreen snapshot={snapshot} brief={brief} />
            <div role="tablist" aria-label="أبواب الغرفة" className={styles.tabs}>
                {DOORS.map((d) => (
                    <button
                        key={d.id}
                        type="button"
                        role="tab"
                        id={`chamber-door-${d.id}`}
                        aria-selected={door === d.id}
                        aria-controls={`chamber-panel-${d.id}`}
                        className={door === d.id ? styles.tabActive : styles.tab}
                        onClick={() => setDoor(d.id)}
                    >
                        {d.label}
                    </button>
                ))}
            </div>
            <div role="tabpanel" id={`chamber-panel-${door}`} aria-labelledby={`chamber-door-${door}`}>
                {door === 'evidence' && <EvidenceDoor snapshot={snapshot} sentences={sentences} />}
                {door === 'challenge' && <ChallengeDoor token={token} questions={questions} />}
                {door === 'prepare' && <PrepareDoor brief={brief} />}
                {door === 'record' && <RecordDoor token={token} brief={brief} vocabulary={vocabulary} />}
            </div>
            <p className={styles.source}>
                المصادر: VALUE_CHAIN.json · CONTACT_LEDGER.csv · OFFER_CATALOG.json · HARD_CURRENCY_SCORECARD.json — تُقرأ
                لحظة الطلب ولا نموذج لغوي في أيّ جملة.
            </p>
        </section>
    );
}
