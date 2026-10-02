"use client";

import React, { useMemo, useState } from 'react';
import styles from './HardCurrencyCenter.module.css';
import { StatusPanel, EmptyState } from './StatusPanel';
import { useHardCurrencyAction, useHardCurrencyResource } from '../../hooks/useHardCurrencyApi';

const SECTOR_LABELS = {
    aluminium: 'الألمنيوم',
    cement: 'الإسمنت',
    fertilisers: 'الأسمدة',
    hydrogen: 'الهيدروجين',
    iron_steel: 'الحديد والصلب',
};

const fmt = (value, digits = 3) =>
    typeof value === 'number' ? value.toLocaleString('fr-FR', { maximumFractionDigits: digits }) : '—';

/**
 * عتبة العبور عبر السنوات (سلسلة واحدة) + رقم المنشأة (خطٌّ مرجعيّ متقطّع بحبرٍ لا بلون).
 * المحور من الصفر · خطّ 2px · علامات 8px · شبكة شعرية · تلميحٌ لكلّ سنة بالحوم والتركيز.
 */
function TrajectoryChart({ trajectory, plant }) {
    const [active, setActive] = useState(null);
    const W = 640;
    const H = 260;
    const M = { top: 20, right: 92, bottom: 32, left: 48 };
    const maxValue = Math.max(...trajectory.map((p) => p.crossover_see_t), plant ?? 0) * 1.15 || 1;
    const innerW = W - M.left - M.right;
    const innerH = H - M.top - M.bottom;
    const x = (i) => M.left + (trajectory.length === 1 ? innerW / 2 : (i * innerW) / (trajectory.length - 1));
    const y = (v) => M.top + innerH - (v / maxValue) * innerH;
    const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * maxValue);
    const line = trajectory.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i)},${y(p.crossover_see_t)}`).join(' ');
    const last = trajectory[trajectory.length - 1];
    const step = trajectory.length > 1 ? innerW / (trajectory.length - 1) : innerW;

    return (
        <figure className={styles.figure}>
            <div className={styles.legend} aria-hidden="true">
                <span><span className={`${styles.legendKey} ${styles.keyThreshold}`} /> عتبة العبور</span>
                {plant != null && <span><span className={`${styles.legendKey} ${styles.keyPlant}`} /> رقم منشأتك</span>}
            </div>
            <div className={styles.chartWrap} dir="ltr">
                <svg viewBox={`0 0 ${W} ${H}`} className={styles.chart} role="img" aria-label="عتبة العبور لكل سنة مقارنةً برقم المنشأة">
                    {ticks.map((t) => (
                        <g key={t}>
                            <line x1={M.left} x2={W - M.right} y1={y(t)} y2={y(t)} className={styles.grid} />
                            <text x={M.left - 6} y={y(t)} className={styles.axisText} textAnchor="end" dominantBaseline="middle">
                                {fmt(t, 2)}
                            </text>
                        </g>
                    ))}
                    {trajectory.map((p, i) => (
                        <text key={p.year} x={x(i)} y={H - 10} className={styles.axisText} textAnchor="middle">
                            {p.year}
                        </text>
                    ))}
                    {plant != null && (
                        <>
                            <line x1={M.left} x2={W - M.right} y1={y(plant)} y2={y(plant)} className={styles.plantLine} />
                            <text x={W - M.right + 6} y={y(plant)} className={styles.directLabel} dominantBaseline="middle">
                                منشأتك {fmt(plant)}
                            </text>
                        </>
                    )}
                    <path d={line} className={styles.thresholdLine} />
                    {trajectory.map((p, i) => (
                        <circle key={p.year} cx={x(i)} cy={y(p.crossover_see_t)} r="4" className={styles.marker} />
                    ))}
                    <text x={x(trajectory.length - 1) + 6} y={y(last.crossover_see_t) - 10} className={styles.directLabel}>
                        العتبة {fmt(last.crossover_see_t)}
                    </text>
                    {active != null && (
                        <line x1={x(active)} x2={x(active)} y1={M.top} y2={M.top + innerH} className={styles.crosshair} />
                    )}
                    {trajectory.map((p, i) => (
                        <rect
                            key={p.year}
                            x={x(i) - step / 2}
                            y={M.top}
                            width={step}
                            height={innerH}
                            className={styles.hit}
                            tabIndex={0}
                            aria-label={`${p.year}: العتبة ${fmt(p.crossover_see_t)} tCO₂e/t`}
                            onPointerEnter={() => setActive(i)}
                            onPointerLeave={() => setActive(null)}
                            onFocus={() => setActive(i)}
                            onBlur={() => setActive(null)}
                        />
                    ))}
                </svg>
                {active != null && (
                    <div
                        className={styles.tooltip}
                        role="status"
                        // فوق السنة المحوَّم عليها، مقيَّداً كي لا يخرج من الإطار.
                        style={{ left: `${Math.min(85, Math.max(15, (x(active) / W) * 100))}%` }}
                    >
                        <strong>{fmt(trajectory[active].crossover_see_t)}</strong> عتبة العبور · {trajectory[active].year}
                        {plant != null && (
                            <div>
                                <strong>{fmt(plant)}</strong> منشأتك —{' '}
                                {plant < trajectory[active].crossover_see_t ? 'البيانات الفعلية أرخص' : 'الافتراضية أرخص'}
                            </div>
                        )}
                    </div>
                )}
            </div>
            <figcaption className={styles.muted}>tCO₂e لكلّ طنّ · المحور يبدأ من الصفر</figcaption>
        </figure>
    );
}

function DetailTable({ detail }) {
    const cert = detail.certificates_default ?? {};
    const toll = detail.path_toll ?? {};
    const cross = detail.crossover ?? {};
    const rows = [
        ['القيمة الافتراضية الجزائرية (مباشر + غير مباشر)', `${fmt(detail.default_see_t.total)} tCO₂e/t`],
        ['بعد علاوة السنة', `${fmt(cross.marked_up_see_t)} tCO₂e/t`],
        ['عتبة العبور', `${fmt(cross.crossover_see_t)} tCO₂e/t`],
        ['رسم المسار (التخلّي عن التخصيص المجاني)', `${fmt(toll.toll_t)} tCO₂e/t · ${fmt(toll.toll_eur_per_t, 2)} €/t`],
        ['كلفة الشهادات بالقيمة الافتراضية', `${fmt(cert.eur_per_t, 2)} €/t (${cert.quarter ?? '—'})`],
    ];
    return (
        <table className={styles.table}>
            <tbody>
                {rows.map(([label, value]) => (
                    <tr key={label}>
                        <th scope="row">{label}</th>
                        <td dir="ltr">{value}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
}

export function CbamDecisionExplorer({ token }) {
    const codes = useHardCurrencyResource(token, '/cbam/codes');
    // The first computable code is the default until the user picks one. Derived, not
    // copied into state from an effect (react-hooks/set-state-in-effect · ISS-211).
    const [chosenCn, setCn] = useState('');
    const defaultCn = useMemo(
        () => codes.data?.codes.find((c) => c.computable)?.cn ?? '',
        [codes.data],
    );
    const cn = chosenCn || defaultCn;
    const [year, setYear] = useState(2026);
    const [plantInput, setPlantInput] = useState('');
    const detail = useHardCurrencyResource(token, cn ? `/cbam/codes/${cn}?year=${year}` : null);
    const decision = useHardCurrencyAction(token);

    const grouped = useMemo(() => {
        const groups = {};
        for (const code of codes.data?.codes ?? []) {
            (groups[code.sector] ??= []).push(code);
        }
        return groups;
    }, [codes.data]);

    if (codes.state !== 'success') {
        return <StatusPanel state={codes.state} message={codes.message} slow={codes.slow} onRetry={codes.reload} />;
    }
    const provenance = codes.data.provenance;
    const plant = decision.state === 'success' ? decision.data?.see_actual_t : null;

    const submit = (event) => {
        event.preventDefault();
        const value = Number(plantInput.replace(',', '.'));
        if (!(value > 0)) return;
        decision.run(`/cbam/codes/${cn}/decision`, { method: 'POST', json: { see_actual: value } });
    };

    return (
        <section aria-labelledby="cbam-title">
            <h3 id="cbam-title" className={styles.sectionTitle}>أداة قرار CBAM — من القيم الرسمية المدبوسة</h3>
            <p className={styles.truthBanner} role="note">
                ترك القيم الافتراضية ليس وفراً تلقائياً: في {provenance.pairs_where_switching_forfeits_credit} من{' '}
                {provenance.route_pairs_pinned} زوجاً مدبوساً يُفقِد الانتقالُ إلى البيانات الفعلية تخصيصاً مجانياً. أداةُ قرارٍ لا
                إعلانٌ رسمي — ورقم المنشأة يُدخله المشتري ولا نملكه.
            </p>
            <div className={styles.filters}>
                <label htmlFor="cbam-code">رمز CN</label>
                <select
                    id="cbam-code"
                    value={cn}
                    onChange={(e) => {
                        setCn(e.target.value);
                        decision.cancel();
                    }}
                >
                    {Object.entries(grouped).map(([sector, items]) => (
                        <optgroup key={sector} label={SECTOR_LABELS[sector] ?? sector}>
                            {items.map((code) => (
                                <option key={code.cn} value={code.cn} disabled={!code.computable}>
                                    {code.cn} — {code.description}
                                    {code.computable ? '' : ' (غير قابل للحساب)'}
                                </option>
                            ))}
                        </optgroup>
                    ))}
                </select>
                <label htmlFor="cbam-year">السنة</label>
                <select id="cbam-year" value={year} onChange={(e) => setYear(Number(e.target.value))}>
                    {provenance.horizon.map((y) => (
                        <option key={y} value={y}>
                            {y}
                        </option>
                    ))}
                </select>
            </div>
            {detail.state !== 'success' ? (
                <StatusPanel state={detail.state} message={detail.message} slow={detail.slow} onRetry={detail.reload} />
            ) : !detail.data.computable ? (
                <EmptyState>لا رقم لهذا الرمز: {detail.data.absent_reason}</EmptyState>
            ) : (
                <>
                    <DetailTable detail={detail.data} />
                    <form className={styles.formInline} onSubmit={submit}>
                        <label htmlFor="cbam-plant">انبعاث منشأتك المقيس (tCO₂e/t)</label>
                        <input
                            id="cbam-plant"
                            inputMode="decimal"
                            value={plantInput}
                            onChange={(e) => setPlantInput(e.target.value)}
                            placeholder="مثلاً 0.6"
                            dir="ltr"
                        />
                        <button type="submit" className={styles.button} disabled={decision.state === 'loading'}>
                            احسب أوّل سنةٍ أرخص
                        </button>
                    </form>
                    <StatusPanel state={decision.state} message={decision.message} slow={decision.slow} />
                    {decision.state === 'success' && decision.data && (
                        <p className={styles.result} aria-live="polite">
                            {decision.data.never_within_horizon
                                ? `برقم ${fmt(decision.data.see_actual_t)}: لا تصير البيانات الفعلية أرخص ضمن الأفق ${provenance.horizon[0]}–${provenance.horizon[provenance.horizon.length - 1]}.`
                                : `برقم ${fmt(decision.data.see_actual_t)}: تصير البيانات الفعلية أرخص ابتداءً من ${decision.data.first_sellable_year}.`}{' '}
                            {decision.data.reading_ar}
                        </p>
                    )}
                    <TrajectoryChart trajectory={detail.data.trajectory} plant={plant} />
                    <details className={styles.details}>
                        <summary>جدول القيم (بديل الرسم)</summary>
                        <table className={styles.table}>
                            <thead>
                                <tr>
                                    <th scope="col">السنة</th>
                                    <th scope="col">عتبة العبور (tCO₂e/t)</th>
                                    {plant != null && <th scope="col">مقارنةً بمنشأتك</th>}
                                </tr>
                            </thead>
                            <tbody>
                                {detail.data.trajectory.map((p) => (
                                    <tr key={p.year}>
                                        <td>{p.year}</td>
                                        <td dir="ltr">{fmt(p.crossover_see_t)}</td>
                                        {plant != null && <td>{plant < p.crossover_see_t ? 'الفعلية أرخص' : 'الافتراضية أرخص'}</td>}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </details>
                </>
            )}
            <p className={styles.source}>
                المصدر: {provenance.source_ar} · بصمة المُدخَلات {String(provenance.inputs_fingerprint).slice(0, 12)}… · ربع{' '}
                {provenance.quarter}
            </p>
        </section>
    );
}
