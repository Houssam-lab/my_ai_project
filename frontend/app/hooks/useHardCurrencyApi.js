"use client";

/**
 * بيانات «مركز العملة الصعبة» (D-305) — منطق الجلب منفصلٌ عن العرض.
 *
 * كلّ طلبٍ بمهلة وإلغاء (AbortController)، و«بطيء» يُعلَن بعد عتبةٍ لا يُترك
 * المستخدم أمام دوّارٍ صامت. والحالات مُسمّاة لا مُستنتَجة:
 *   loading · success · error · forbidden · unavailable (503 بسببه من الخادم).
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { readApiError } from '../utils/apiError';

const API_ORIGIN = process.env.NEXT_PUBLIC_API_URL ?? '';
export const HARD_CURRENCY_BASE = '/admin/api/hard-currency';
const TIMEOUT_MS = 30000;
const SLOW_MS = 4000;

function stateForStatus(status) {
    if (status === 401 || status === 403) return 'forbidden';
    if (status === 503) return 'unavailable';
    return 'error';
}

/** طلبٌ واحد بمهلة — يُرجِع {ok, status, data, message}. لا يرمي إلّا عند الإلغاء الصريح. */
export async function hardCurrencyRequest(token, path, { method = 'GET', json, form, signal } = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
    const onAbort = () => controller.abort();
    signal?.addEventListener('abort', onAbort);
    const headers = { Authorization: `Bearer ${token}` };
    let body;
    if (json !== undefined) {
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify(json);
    } else if (form !== undefined) {
        body = form;
    }
    try {
        const res = await fetch(`${API_ORIGIN}${HARD_CURRENCY_BASE}${path}`, {
            method,
            headers,
            body,
            signal: controller.signal,
        });
        if (res.ok) {
            return { ok: true, status: res.status, data: await res.json(), message: '' };
        }
        const message = await readApiError(res, 'تعذّر تنفيذ الطلب.');
        return { ok: false, status: res.status, data: null, message };
    } catch (error) {
        if (signal?.aborted) throw error;
        const timedOut = controller.signal.aborted;
        return {
            ok: false,
            status: 0,
            data: null,
            message: timedOut
                ? 'استغرق الخادم وقتاً أطول من المتوقّع. حاول مرّة أخرى.'
                : 'تعذّر الاتصال بالخادم. تحقّق من الشبكة وحاول مرّة أخرى.',
        };
    } finally {
        clearTimeout(timer);
        signal?.removeEventListener('abort', onAbort);
    }
}

/** مورد قراءة: يُجلَب عند التركيب وعند تغيّر المسار أو الرمز. */
export function useHardCurrencyResource(token, path) {
    const [data, setData] = useState(null);
    const [message, setMessage] = useState('');
    const [nonce, setNonce] = useState(0);
    // Each request has a key. «Loading» and «slow» are derived from whether the last
    // answer belongs to the current key — never reset synchronously inside the effect
    // (react-hooks/set-state-in-effect · ISS-211). An answer for an older key never
    // shows as current, and the last good data stays visible while a reload runs.
    const requestKey = path ? `${nonce}\u0000${path}\u0000${token ?? ''}` : null;
    const [settled, setSettled] = useState({ key: null, state: 'loading' });
    const [slowKey, setSlowKey] = useState(null);

    useEffect(() => {
        if (!requestKey) return undefined;
        const controller = new AbortController();
        const slowTimer = setTimeout(() => setSlowKey(requestKey), SLOW_MS);
        hardCurrencyRequest(token, path, { signal: controller.signal })
            .then((result) => {
                if (controller.signal.aborted) return;
                if (result.ok) {
                    setData(result.data);
                    setSettled({ key: requestKey, state: 'success' });
                } else {
                    setMessage(result.message);
                    setSettled({ key: requestKey, state: stateForStatus(result.status) });
                }
            })
            .catch(() => {})
            .finally(() => clearTimeout(slowTimer));
        return () => {
            controller.abort();
            clearTimeout(slowTimer);
        };
    }, [requestKey, token, path]);

    const reload = useCallback(() => setNonce((n) => n + 1), []);
    const current = requestKey !== null && settled.key === requestKey;
    return {
        state: current ? settled.state : 'loading',
        data,
        message,
        slow: !current && slowKey === requestKey,
        reload,
    };
}

/** فعلٌ يُطلَق بيد المستخدم (رفع ملف · حساب قرار). */
export function useHardCurrencyAction(token) {
    const [state, setState] = useState('idle');
    const [data, setData] = useState(null);
    const [message, setMessage] = useState('');
    const [slow, setSlow] = useState(false);
    const controllerRef = useRef(null);

    useEffect(() => () => controllerRef.current?.abort(), []);

    const run = useCallback(
        async (path, options) => {
            controllerRef.current?.abort();
            const controller = new AbortController();
            controllerRef.current = controller;
            const slowTimer = setTimeout(() => setSlow(true), SLOW_MS);
            setState('loading');
            setSlow(false);
            setMessage('');
            try {
                const result = await hardCurrencyRequest(token, path, {
                    ...options,
                    signal: controller.signal,
                });
                if (result.ok) {
                    setData(result.data);
                    setState('success');
                } else {
                    setData(null);
                    setMessage(result.message);
                    setState(stateForStatus(result.status));
                }
            } catch {
                // أُلغي الطلب لصالح طلبٍ أحدث — لا حالة تُعرَض.
            } finally {
                clearTimeout(slowTimer);
            }
        },
        [token],
    );

    const cancel = useCallback(() => {
        controllerRef.current?.abort();
        setState('idle');
        setSlow(false);
    }, []);

    return { state, data, message, slow, run, cancel };
}
