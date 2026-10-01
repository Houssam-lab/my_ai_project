"use client";

import React from 'react';
import styles from './HardCurrencyCenter.module.css';
import { EmptyState } from './StatusPanel';

/** الأصناف تُعرَض بجذرها وحالة نشرها وسببها — والمسابير نفسها لا تُعاد (L5). */
export function RedTeamClasses({ data }) {
    const probe = data.external_probe;
    return (
        <section aria-labelledby="redteam-title">
            <h3 id="redteam-title" className={styles.sectionTitle}>أصناف الاختراق العربي/الفرنسي</h3>
            <p className={styles.truthBanner} role="note">
                {data.publishable_count} من {data.classes.length} أصناف قابلة للنشر. الأصناف مستخرجة من حوادث المنصّة التعليمية؛ ولا
                يُنشَر صنفٌ مصدره حادثةٌ ما زالت مفتوحة.
            </p>
            {probe && (
                <div className={styles.card}>
                    <div className={styles.subhead}>نتيجةٌ على نظامٍ لم نكتبه ({probe.decision})</div>
                    <div>
                        الهدف: <code className={styles.evidence}>{probe.target_package}</code> · أصنافٌ مقيسة{' '}
                        {Array.isArray(probe.classes_measured) ? probe.classes_measured.length : probe.classes_measured} · منتهَكة{' '}
                        {Array.isArray(probe.classes_violated) ? probe.classes_violated.length : probe.classes_violated}
                    </div>
                    {probe.honest_limits_ar && (
                        <div className={styles.muted}>
                            الحدّ: {Array.isArray(probe.honest_limits_ar) ? probe.honest_limits_ar.join(' · ') : String(probe.honest_limits_ar)}
                        </div>
                    )}
                </div>
            )}
            {data.classes.length === 0 ? (
                <EmptyState>لا أصناف في الذخيرة.</EmptyState>
            ) : (
                <ul className={styles.cardList}>
                    {data.classes.map((item) => (
                        <li key={item.class_id} className={styles.card}>
                            <div className={styles.cardHeader}>
                                <div>
                                    <span className={styles.pathId}>{item.class_id}</span> <strong>{item.title_ar}</strong>
                                </div>
                                <span className={`${styles.badge} ${item.publishable ? styles.badge_validated_capability : styles.badgeMuted}`}>
                                    {item.publishable ? 'قابل للنشر' : 'محجوب'}
                                </span>
                            </div>
                            <p className={styles.muted} dir="ltr">
                                {item.root_cause}
                            </p>
                            {!item.publishable && item.publish_block_reason_ar && (
                                <p className={styles.warning}>{item.publish_block_reason_ar}</p>
                            )}
                            <div className={styles.muted}>
                                المصادر:{' '}
                                {item.sources.map((s) => `${s.id} (${s.status})`).join(' · ')}
                            </div>
                        </li>
                    ))}
                </ul>
            )}
        </section>
    );
}
