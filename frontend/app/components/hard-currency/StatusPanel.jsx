"use client";

import React from 'react';
import styles from './HardCurrencyCenter.module.css';

/**
 * حالةٌ غير النجاح تُعلَن بنصّها — لا شاشةٌ فارغة تُقرأ «لا شيء» (§0).
 * `unavailable` = 503 بسببٍ من الخادم: مصدرٌ غائب في هذا النشر، لا عطلٌ عابر.
 */
export function StatusPanel({ state, message, slow, onRetry, onCancel }) {
    if (state === 'loading') {
        return (
            <div className={styles.status} role="status" aria-live="polite">
                <span>جارٍ التحميل…</span>
                {slow && (
                    <span className={styles.muted}>
                        {' '}الاتصال بطيء — ما زلنا ننتظر الخادم.
                        {onCancel && (
                            <button type="button" className={styles.linkButton} onClick={onCancel}>
                                إلغاء
                            </button>
                        )}
                    </span>
                )}
            </div>
        );
    }
    const titles = {
        forbidden: 'لا تملك صلاحية هذا القسم — للمدير وحده.',
        unavailable: 'المصدر غير متاح في هذا النشر.',
        error: 'تعذّر تحميل البيانات.',
    };
    if (!titles[state]) return null;
    return (
        <div className={styles.statusError} role="alert">
            <strong>{titles[state]}</strong>
            {message && <p className={styles.muted}>{message}</p>}
            {onRetry && state !== 'forbidden' && (
                <button type="button" className={styles.button} onClick={onRetry}>
                    إعادة المحاولة
                </button>
            )}
        </div>
    );
}

export function EmptyState({ children }) {
    return <p className={styles.empty}>{children}</p>;
}
