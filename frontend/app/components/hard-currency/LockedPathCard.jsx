"use client";

import React from 'react';
import styles from './HardCurrencyCenter.module.css';

/** امتدادٌ مقفل يُكتب بشرط فتحه — الطموح يُصنَّف ولا يُكتَم (D-209). */
export function LockedPathCard({ extension }) {
    return (
        <div className={styles.locked}>
            <div className={styles.lockedTitle}>
                <i className="fas fa-lock" aria-hidden="true"></i> {extension.title_ar}
            </div>
            <div className={styles.muted}>شرط الفتح: {extension.unlock_ar}</div>
            {extension.constraint_ar && <div className={styles.muted}>{extension.constraint_ar}</div>}
        </div>
    );
}
