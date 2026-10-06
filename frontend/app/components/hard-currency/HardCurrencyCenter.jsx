"use client";

/**
 * «مركز العملة الصعبة» (D-305) — للمدير وحده. يُفتح على «غرفة القرار» (D-314): أقصى ما يُقال
 * وأوّل دليلٍ ناقص وفعلٌ بشريٌّ واحد — قبل أيّ خريطةٍ أو ورشة.
 *
 * كلّ رقمٍ هنا يُظهر مصدره، وكلّ مسارٍ يُظهر موقعه الحقيقي على سلسلة القيمة والحلقةَ
 * التالية ومن يسدّها. ⛔ لا يُوصَف شيءٌ «ثورياً» ما دام التصنيف دون الدليل التجاري.
 */

import React, { useRef, useState } from 'react';
import styles from './HardCurrencyCenter.module.css';
import { StatusPanel } from './StatusPanel';
import { FrontierMap } from './FrontierMap';
import { EinvoicingWorkbench } from './EinvoicingWorkbench';
import { CbamDecisionExplorer } from './CbamDecisionExplorer';
import { RedTeamClasses } from './RedTeamClasses';
import { DecisionChamber } from './DecisionChamber';
import { useHardCurrencyResource } from '../../hooks/useHardCurrencyApi';

const TABS = [
    { id: 'chamber', label: 'غرفة القرار' },
    { id: 'frontier', label: 'خريطة الجبهة' },
    { id: 'einvoicing', label: 'ورشة الفوترة' },
    { id: 'cbam', label: 'قرار CBAM' },
    { id: 'redteam', label: 'أصناف الاختراق' },
];

function FrontierTab({ token, onOpenWorkbench }) {
    const frontier = useHardCurrencyResource(token, '/frontier');
    if (frontier.state !== 'success') {
        return <StatusPanel state={frontier.state} message={frontier.message} slow={frontier.slow} onRetry={frontier.reload} />;
    }
    return <FrontierMap data={frontier.data} onOpenWorkbench={onOpenWorkbench} />;
}

function ChamberTab({ token }) {
    const chamber = useHardCurrencyResource(token, '/chamber');
    if (chamber.state !== 'success') {
        return <StatusPanel state={chamber.state} message={chamber.message} slow={chamber.slow} onRetry={chamber.reload} />;
    }
    return <DecisionChamber token={token} data={chamber.data} />;
}

function RedTeamTab({ token }) {
    const classes = useHardCurrencyResource(token, '/redteam/classes');
    if (classes.state !== 'success') {
        return <StatusPanel state={classes.state} message={classes.message} slow={classes.slow} onRetry={classes.reload} />;
    }
    return <RedTeamClasses data={classes.data} />;
}

export default function HardCurrencyCenter({ token, onBack }) {
    const [tab, setTab] = useState('chamber');
    const tabRefs = useRef({});

    const onKeyDown = (event) => {
        const index = TABS.findIndex((t) => t.id === tab);
        // RTL: السهم الأيسر يتقدّم.
        const delta = event.key === 'ArrowLeft' ? 1 : event.key === 'ArrowRight' ? -1 : 0;
        if (!delta) return;
        event.preventDefault();
        const next = TABS[(index + delta + TABS.length) % TABS.length].id;
        setTab(next);
        tabRefs.current[next]?.focus();
    };

    return (
        <div className={styles.center} dir="rtl">
            <div className={styles.centerHeader}>
                <h2 className={styles.centerTitle}>مركز العملة الصعبة</h2>
                <button type="button" className={styles.buttonSecondary} onClick={onBack}>
                    العودة إلى المحادثة
                </button>
            </div>
            <div role="tablist" aria-label="أقسام المركز" className={styles.tabs} onKeyDown={onKeyDown}>
                {TABS.map((t) => (
                    <button
                        key={t.id}
                        ref={(el) => {
                            tabRefs.current[t.id] = el;
                        }}
                        type="button"
                        role="tab"
                        id={`hc-tab-${t.id}`}
                        aria-selected={tab === t.id}
                        aria-controls={`hc-panel-${t.id}`}
                        tabIndex={tab === t.id ? 0 : -1}
                        className={tab === t.id ? styles.tabActive : styles.tab}
                        onClick={() => setTab(t.id)}
                    >
                        {t.label}
                    </button>
                ))}
            </div>
            <div role="tabpanel" id={`hc-panel-${tab}`} aria-labelledby={`hc-tab-${tab}`} className={styles.panel}>
                {tab === 'chamber' && <ChamberTab token={token} />}
                {tab === 'frontier' && <FrontierTab token={token} onOpenWorkbench={setTab} />}
                {tab === 'einvoicing' && <EinvoicingWorkbench token={token} />}
                {tab === 'cbam' && <CbamDecisionExplorer token={token} />}
                {tab === 'redteam' && <RedTeamTab token={token} />}
            </div>
        </div>
    );
}
