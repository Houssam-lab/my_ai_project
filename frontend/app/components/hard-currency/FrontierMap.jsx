"use client";

import React, { useMemo, useState } from 'react';
import styles from './HardCurrencyCenter.module.css';
import { LockedPathCard } from './LockedPathCard';
import { EmptyState } from './StatusPanel';

export const CLASSIFICATION_LABELS = {
    unevidenced_hypothesis: 'فرضيةٌ بلا دليل',
    research_asset: 'أصلٌ بحثي',
    engineering_capability: 'قدرةٌ هندسية',
    validated_capability: 'قدرةٌ مُثبَتة على نظامٍ مستقلّ',
    commercial_evidence: 'دليلٌ تجاري',
};
const CLASSIFICATION_ORDER = Object.keys(CLASSIFICATION_LABELS);
const ACTOR_LABELS = { human: 'إنسان', code: 'كود' };
const WORKBENCH_LABELS = {
    einvoicing: 'افتح ورشة الفوترة',
    cbam: 'افتح أداة قرار CBAM',
    redteam: 'افتح أصناف الاختراق',
};

/** ثماني حلقات: المُحتسَبة ممتلئة، والمُسجَّلة بعد فجوةٍ مفرغة، والناقصة باهتة. */
function ChainDots({ path }) {
    const raw = new Set(path.links.filter((l) => l.status === 'REACHED').map((l) => l.number));
    return (
        <span
            className={styles.chain}
            role="img"
            aria-label={`الحلقات المُحتسَبة ${path.reached} من 8`}
        >
            {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => {
                const kind = n <= path.reached ? styles.dotReached : raw.has(n) ? styles.dotGap : styles.dotMissing;
                return <span key={n} className={`${styles.dot} ${kind}`} aria-hidden="true" />;
            })}
        </span>
    );
}

function LinkRow({ link, title }) {
    const reached = link.status === 'REACHED';
    return (
        <li className={styles.linkRow}>
            <span className={reached ? styles.ok : styles.missing}>
                {reached ? '✓' : '○'} {link.number}. {title}
            </span>
            {reached
                ? link.evidence.map((ev) => (
                      <code key={ev} className={styles.evidence}>
                          {ev}
                      </code>
                  ))
                : link.reason_ar && <span className={styles.muted}> — {link.reason_ar}</span>}
            {link.note_ar && <div className={styles.muted}>{link.note_ar}</div>}
        </li>
    );
}

function PathCard({ path, linkTitles, onOpenWorkbench }) {
    const [open, setOpen] = useState(false);
    const detailsId = `path-details-${path.id}`;
    return (
        <li className={styles.card}>
            <div className={styles.cardHeader}>
                <div>
                    <span className={styles.pathId}>{path.id}</span> <strong>{path.title_ar}</strong>
                    {path.withdrawn && <span className={styles.badgeMuted}>مسحوب</span>}
                </div>
                <span className={`${styles.badge} ${styles[`badge_${path.classification}`] ?? ''}`}>
                    {CLASSIFICATION_LABELS[path.classification] ?? path.classification}
                </span>
            </div>
            <ChainDots path={path} />
            <div className={styles.nextLine}>
                {path.next_link ? (
                    <>
                        الحلقة التالية الناقصة: <strong>{path.next_link}. {path.next_link_title_ar}</strong>
                        {' · '}يسدّها: <strong>{ACTOR_LABELS[path.next_actor] ?? path.next_actor}</strong>
                    </>
                ) : (
                    <strong>السلسلة مكتملة</strong>
                )}
            </div>
            {path.owner_decision && <div className={styles.muted}>قرار المالك: {path.owner_decision}</div>}
            <div className={styles.actions}>
                <button
                    type="button"
                    className={styles.linkButton}
                    aria-expanded={open}
                    aria-controls={detailsId}
                    onClick={() => setOpen((v) => !v)}
                >
                    {open ? 'إخفاء الأدلّة' : 'عرض الأدلّة'}
                </button>
                {path.workbench && WORKBENCH_LABELS[path.workbench] && (
                    <button type="button" className={styles.button} onClick={() => onOpenWorkbench(path.workbench)}>
                        {WORKBENCH_LABELS[path.workbench]}
                    </button>
                )}
            </div>
            {open && (
                <div id={detailsId} className={styles.details}>
                    <ol className={styles.linkList}>
                        {path.links.map((link) => (
                            <LinkRow key={link.number} link={link} title={linkTitles[link.number]} />
                        ))}
                    </ol>
                    {path.reused_assets.length > 0 && (
                        <div>
                            <div className={styles.subhead}>ما يعيد هذا المسار استعماله</div>
                            <ul className={styles.plainList}>
                                {path.reused_assets.map((asset) => (
                                    <li key={asset.path}>
                                        <code className={styles.evidence}>{asset.path}</code> — {asset.role_ar}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                    {path.locked_extensions.map((ext) => (
                        <LockedPathCard key={ext.title_ar} extension={ext} />
                    ))}
                </div>
            )}
        </li>
    );
}

export function FrontierMap({ data, onOpenWorkbench }) {
    const [filter, setFilter] = useState('all');
    const linkTitles = useMemo(
        () => Object.fromEntries(data.links.map((l) => [l.number, l.title_ar])),
        [data.links],
    );
    const paths = filter === 'all' ? data.paths : data.paths.filter((p) => p.classification === filter);
    const funnel = data.funnel ?? {};
    const commercial = data.by_classification.commercial_evidence ?? 0;

    return (
        <section aria-labelledby="frontier-title">
            <h3 id="frontier-title" className={styles.sectionTitle}>خريطة الجبهة</h3>
            <div className={styles.truthBanner} role="note">
                {commercial === 0
                    ? `لا دليلَ تجاريّاً في أيّ مسارٍ بعد: ${funnel.contacts_sent ?? 0} اتصال · ${funnel.replies_received ?? 0} ردّ · ${funnel.payments_settled ?? 0} دفعة مسوّاة · GATE_C = ${data.gate_c ?? '؟'}.`
                    : `${commercial} مسار بدليلٍ تجاري.`}{' '}
                الحلقة التالية بشرية في {data.next_actor_human} مساراً وبرمجية في {data.next_actor_code}.
            </div>
            <dl className={styles.tiles}>
                {CLASSIFICATION_ORDER.map((key) => (
                    <div key={key} className={styles.tile}>
                        <dt>{CLASSIFICATION_LABELS[key]}</dt>
                        <dd>{data.by_classification[key] ?? 0}</dd>
                    </div>
                ))}
            </dl>
            {!data.committed_snapshot_current && (
                <p className={styles.warning} role="note">
                    اللقطة المُلتزَمة في VALUE_CHAIN.json لا تطابق الاشتقاق الحيّ — المعروض هنا هو الاشتقاق الحيّ.
                </p>
            )}
            <div className={styles.filters}>
                <label htmlFor="frontier-filter">التصنيف</label>
                <select id="frontier-filter" value={filter} onChange={(e) => setFilter(e.target.value)}>
                    <option value="all">الكلّ ({data.paths.length})</option>
                    {CLASSIFICATION_ORDER.map((key) => (
                        <option key={key} value={key}>
                            {CLASSIFICATION_LABELS[key]} ({data.by_classification[key] ?? 0})
                        </option>
                    ))}
                </select>
                <span className={styles.muted}>آخر حدثٍ في سجلّ الاتصال: {data.as_of ?? '—'}</span>
            </div>
            {paths.length === 0 ? (
                <EmptyState>لا مسار في هذا التصنيف.</EmptyState>
            ) : (
                <ul className={styles.cardList}>
                    {paths.map((path) => (
                        <PathCard key={path.id} path={path} linkTitles={linkTitles} onOpenWorkbench={onOpenWorkbench} />
                    ))}
                </ul>
            )}
        </section>
    );
}
