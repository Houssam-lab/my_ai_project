"use client";

import React, { useRef, useState } from 'react';
import styles from './HardCurrencyCenter.module.css';
import { StatusPanel, EmptyState } from './StatusPanel';
import { useHardCurrencyAction } from '../../hooks/useHardCurrencyApi';

const MAX_BYTES = 2 * 1024 * 1024;
const VISIBLE_ANOMALIES = 50;
const SUMMARY_LABELS = {
    total: 'السجلّات',
    valides: 'سليمة',
    erreurs_siren: 'أخطاء SIREN',
    erreurs_siret: 'أخطاء SIRET',
    erreurs_tva: 'أخطاء TVA',
    erreurs_bce: 'أخطاء BCE',
    doublons: 'مكرّرة',
};

function download(filename, text, type) {
    // BOM يجعل Excel يقرأ UTF-8 بالعربية/الفرنسية سليماً.
    const blob = new Blob(['﻿', text], { type });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
}

function AuditResult({ result }) {
    const [showAll, setShowAll] = useState(false);
    const anomalies = showAll ? result.anomalies : result.anomalies.slice(0, VISIBLE_ANOMALIES);
    const tiles = Object.entries(SUMMARY_LABELS).filter(([key]) => key in result.summary);
    return (
        <div className={styles.result} aria-live="polite">
            <p className={styles.muted}>
                {result.filename} · الممرّ {result.corridor.toUpperCase()} · الملفّ لم يُخزَّن · بلا تحقّقٍ عبر الشبكة
            </p>
            <dl className={styles.tiles}>
                {tiles.map(([key, label]) => (
                    <div key={key} className={styles.tile}>
                        <dt>{label}</dt>
                        <dd>{result.summary[key]}</dd>
                    </div>
                ))}
            </dl>
            <div className={styles.actions}>
                <button
                    type="button"
                    className={styles.button}
                    onClick={() => download(result.cleaned_filename, result.cleaned_csv, 'text/csv;charset=utf-8')}
                >
                    تنزيل الملفّ المنظَّف
                </button>
                <button
                    type="button"
                    className={styles.buttonSecondary}
                    onClick={() =>
                        download(result.cleaned_filename.replace(/\.csv$/i, '_RAPPORT.md'), result.report_markdown, 'text/markdown;charset=utf-8')
                    }
                >
                    تنزيل التقرير
                </button>
            </div>
            {result.anomalies.length === 0 ? (
                <EmptyState>لا شذوذ: كلّ السجلّات سليمة بهذه الفحوص.</EmptyState>
            ) : (
                <div className={styles.tableWrap}>
                    <table className={styles.table}>
                        <caption className={styles.muted}>
                            الشذوذات ({result.anomalies.length}
                            {result.anomalies_truncated ? '+ — قُصّت القائمة، والملفّ المنظَّف كامل' : ''})
                        </caption>
                        <thead>
                            <tr>
                                <th scope="col">السطر</th>
                                <th scope="col">الاسم</th>
                                <th scope="col">المعرّف</th>
                                <th scope="col">الأخطاء</th>
                            </tr>
                        </thead>
                        <tbody>
                            {anomalies.map((item) => (
                                <tr key={`${item.ligne}-${item.nom}`}>
                                    <td>{item.ligne}</td>
                                    <td>{item.nom}</td>
                                    <td dir="ltr">{item.siren ?? item.bce ?? ''}</td>
                                    <td dir="ltr">{(item.erreurs ?? []).join(' · ')}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {result.anomalies.length > VISIBLE_ANOMALIES && (
                        <button type="button" className={styles.linkButton} onClick={() => setShowAll((v) => !v)}>
                            {showAll ? 'عرض أقلّ' : `عرض الكلّ (${result.anomalies.length})`}
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}

export function EinvoicingWorkbench({ token }) {
    const [corridor, setCorridor] = useState('fr');
    const [localError, setLocalError] = useState('');
    const fileRef = useRef(null);
    const action = useHardCurrencyAction(token);

    const submit = (event) => {
        event.preventDefault();
        const file = fileRef.current?.files?.[0];
        if (!file) {
            setLocalError('اختر ملفّ CSV أوّلاً.');
            return;
        }
        if (!file.name.toLowerCase().endsWith('.csv')) {
            setLocalError('CSV فقط — صدّر ملفّ Excel إلى CSV أوّلاً.');
            return;
        }
        if (file.size > MAX_BYTES) {
            setLocalError('الملفّ أكبر من 2 م.ب — قسّمه.');
            return;
        }
        setLocalError('');
        const form = new FormData();
        form.append('file', file);
        form.append('corridor', corridor);
        action.run('/einvoicing-audits', { method: 'POST', form });
    };

    return (
        <section aria-labelledby="einvoicing-title">
            <h3 id="einvoicing-title" className={styles.sectionTitle}>ورشة الفوترة الإلكترونية FR/BE</h3>
            <p className={styles.muted}>
                تدقيقٌ حتميّ لملفّ أطرافٍ ثالثة بأدوات المنتج النشط. الملفّ يُعالَج في الذاكرة ولا يُخزَّن، ولا نموذج لغوي
                في الأرقام.
            </p>
            <form className={styles.form} onSubmit={submit}>
                <fieldset className={styles.fieldset}>
                    <legend>الممرّ</legend>
                    <label>
                        <input type="radio" name="corridor" value="fr" checked={corridor === 'fr'} onChange={() => setCorridor('fr')} />{' '}
                        فرنسا (SIREN · SIRET · TVA)
                    </label>
                    <label>
                        <input type="radio" name="corridor" value="be" checked={corridor === 'be'} onChange={() => setCorridor('be')} />{' '}
                        بلجيكا (BCE · Peppol)
                    </label>
                </fieldset>
                <label htmlFor="einvoicing-file">ملفّ CSV (حتى 2 م.ب · 5000 سطر)</label>
                <input id="einvoicing-file" ref={fileRef} type="file" accept=".csv,text/csv" />
                <button type="submit" className={styles.button} disabled={action.state === 'loading'}>
                    {action.state === 'loading' ? 'جارٍ التدقيق…' : 'دقّق الملفّ'}
                </button>
            </form>
            {localError && (
                <p className={styles.statusError} role="alert">
                    {localError}
                </p>
            )}
            <StatusPanel state={action.state} message={action.message} slow={action.slow} onCancel={action.cancel} />
            {action.state === 'success' && action.data && <AuditResult result={action.data} />}
        </section>
    );
}
