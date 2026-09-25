<script lang="ts">
    import { onMount } from 'svelte';
    import {
        app,
        appVersion,
        defaultApp,
        initializeApp,
        choiceMap,
        pointTypeMap,
        rowMap,
        variableMap,
        checkRequirements,
        selectObject,
        deselectObject,
        selectedOneMore,
        selectedOneLess,
        cleanActivated,
        getSelectedObjectId,
    } from '$lib/store/store.svelte';

    let output = 'running';

    const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value));
    const options = () => ({ linkedObjects: [] as string[] });

    function exactDefaultExport(): string {
        const value: any = clone(defaultApp);
        // AppSaveLoad.svelte saveToDisk() mutates app.activated this way first.
        value.activated = ''.split(',');
        value.version = appVersion;
        return JSON.stringify(value);
    }

    function selectableEntries(): Array<[string, any]> {
        const out: Array<[string, any]> = [];
        for (const row of [...app.rows, ...app.backpack]) {
            for (const choice of row.objects || []) {
                out.push([choice.id, choice]);
                for (const addon of choice.addons || []) {
                    if (addon.isSelectable) out.push([addon.id, addon]);
                }
            }
        }
        return out;
    }

    function snapshot(checkIds: string[]) {
        const entities: Record<string, any> = {};
        for (const [id, entity] of selectableEntries()) {
            entities[id] = {
                active: !!entity.isActive,
                multiple: Number(entity.multipleUseVariable ?? 0),
            };
        }
        const points: Record<string, number> = {};
        for (const point of app.pointTypes) points[point.id] = Number(point.startingSum);
        const variables: Record<string, boolean> = {};
        for (const variable of app.variables) variables[variable.id] = !!variable.isTrue;
        const words: Record<string, string> = {};
        for (const word of app.words) words[word.id] = String(word.replaceText ?? '');
        const rows: Record<string, any> = {};
        for (const row of [...app.rows, ...app.backpack]) {
            rows[row.id] = {
                currentChoices: Number(row.currentChoices || 0),
                allowedChoices: Number(row.allowedChoices || 0),
            };
        }
        const requirements: Record<string, boolean> = {};
        for (const id of checkIds) {
            const item = choiceMap.get(id);
            if (item) requirements[id] = checkRequirements(item.choice.requireds);
        }
        return { entities, points, variables, words, rows, requirements, buildString: getSelectedObjectId() };
    }

    async function act(action: any) {
        if (action.op === 'set_point') {
            const point = pointTypeMap.get(String(action.id));
            if (point) point.startingSum = Number(action.value);
            return;
        }
        if (action.op === 'reset') {
            await cleanActivated();
            return;
        }
        const item = choiceMap.get(String(action.id));
        if (!item) throw new Error(`missing choice ${action.id}`);
        const entity: any = item.choice;
        if (action.op === 'select') {
            if (entity.isSelectableMultiple) await selectedOneMore(entity, item.row, options());
            else await selectObject(entity, item.row, options());
            return;
        }
        if (action.op === 'deselect') {
            if (entity.isSelectableMultiple) await selectedOneLess(entity, item.row, options());
            else await deselectObject(entity, item.row, options());
            return;
        }
        throw new Error(`unsupported action ${action.op}`);
    }

    onMount(async () => {
        try {
            localStorage.clear();
            const emptySelectedObjectId = getSelectedObjectId();
            const response = await fetch('./parity-fixtures.json', { cache: 'no-store' });
            const payload = await response.json();
            const results: Record<string, any> = {};
            for (const testCase of payload.cases) {
                localStorage.clear();
                await initializeApp(clone(testCase.project));
                for (const action of testCase.actions || []) await act(action);
                results[testCase.name] = snapshot(testCase.check_requirements || []);
            }
            output = JSON.stringify({
                commit: payload.commit,
                appVersion,
                defaultExport: exactDefaultExport(),
                emptySelectedObjectId,
                results,
            });
            document.title = 'ICCPLUS_PARITY_DONE';
        } catch (error) {
            output = JSON.stringify({ error: String(error), stack: error instanceof Error ? error.stack : '' });
            document.title = 'ICCPLUS_PARITY_ERROR';
        }
    });
</script>

<pre id="parity-results">{output}</pre>
