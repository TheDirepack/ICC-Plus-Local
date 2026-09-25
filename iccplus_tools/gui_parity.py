from __future__ import annotations

from typing import Any

from .field_catalog import catalog_kinds
from .version import __version__

SOURCE_COMMIT = '1ea9db888cde2286d18d0d5de50933cb8773b739'

# This inventory describes authoring outcomes and Creator actions. Browser-only
# presentation controls that do not change project data are called out rather
# than silently counted as authoring features.
_FEATURES: list[dict[str, Any]] = [
    {'feature':'project.save_json','status':'complete','script':'format --style creator / ordinary project writes','source':'AppSaveLoad.svelte saveToDisk'},
    {'feature':'project.load_json','status':'complete','script':'all PROJECT commands accept project.json','source':'AppSaveLoad.svelte loadFromDisk'},
    {'feature':'project.save_slots','status':'equivalent','script':'copy/version project files in the filesystem','source':'AppSaveLoad.svelte saveApp/loadApp/removeSave','note':'IndexedDB slot storage is browser-local UI state, not project format.'},
    {'feature':'project.autosave','status':'equivalent','script':'filesystem/editor autosave or version-control workflow','source':'store.svelte.ts autoSave','note':'Browser IndexedDB scheduling is not copied into the CLI.'},
    {'feature':'project.project_stats','status':'complete','script':'project-stats PROJECT','source':'AppProjectStats.svelte'},
    {'feature':'project.defaults','status':'complete','script':'update/set project default* fields; fields project --details','source':'Features/AppDefaults.svelte'},
    {'feature':'project.ids_from_titles','status':'complete','script':'ids-from-titles PROJECT','source':'Features/AppDefaults.svelte idToTitle','note':'Uses the Creator title conversion and _dup rule, but safely rewrites references instead of leaving stale IDs.'},
    {'feature':'project.viewer_config','status':'complete','script':'update project viewerConfig or typed set path','source':'AppViewerConfig.svelte'},
    {'feature':'project.global_styling','status':'complete','script':'style manifest; fields styling --details','source':'Creator styling dialogs'},
    {'feature':'project.style_templates','status':'complete','script':'style-template list|show|apply','source':'Features/AppTemplates.svelte','note':'Includes all eight pinned 2.10.7 presets and applies them with Creator-compatible merge semantics.'},
    {'feature':'project.custom_css','status':'complete','script':'style manifest project.customCSS/customCSSAppend','source':'AppCustomCSS.svelte'},
    {'feature':'project.fonts','status':'complete','script':'fonts list|add|remove','source':'AppGlobalSettings.svelte importFont/deleteFont','note':'Edits the same googleFonts/customFonts project arrays. Browser CORS/font loading is verified only in the real Viewer.'},
    {'feature':'project.id_name_csv','status':'complete','script':'id-csv PROJECT','source':'Features/AppIdSearch.svelte exportAsCsv','note':'Matches the Creator BOM CSV and its normal-Row-only scope.'},
    {'feature':'project.search_navigation','status':'complete','script':'search/list/show','source':'AppSearchForm.svelte and Row/Object list dialogs'},
    {'feature':'project.symbol_reference','status':'complete','script':'symbols','source':'Features/AppSymbols.svelte','note':'Returns the exact pinned symbol list.'},

    {'feature':'rows.create_edit_delete','status':'complete','script':'add/update/delete row','source':'AppRowList.svelte'},
    {'feature':'backpack_rows.create_edit_delete','status':'complete','script':'add/update/delete backpack_row','source':'AppBackpack.svelte'},
    {'feature':'choices.create_edit_delete','status':'complete','script':'add/update/delete choice; add choice --count N for Creator-style multi-create','source':'AppObjectList.svelte'},
    {'feature':'addons.create_edit_delete','status':'complete','script':'add/update/delete addon|selectable_addon','source':'ObjectAddon.svelte'},
    {'feature':'scores.create_edit_delete','status':'complete','script':'add/update/delete score','source':'ObjectScore.svelte'},
    {'feature':'requirements.create_edit_delete','status':'complete','script':'add/update/delete requirement plus require/exclude/gate operations','source':'ObjectRequired.svelte'},
    {'feature':'points.create_edit_delete','status':'complete','script':'add/update/delete point','source':'Features/AppPoints.svelte'},
    {'feature':'variables.create_edit_delete','status':'complete','script':'add/update/delete variable','source':'Features/AppVariables.svelte'},
    {'feature':'words.create_edit_delete','status':'complete','script':'add/update/delete word','source':'Features/AppWords.svelte'},
    {'feature':'groups.create_edit_delete','status':'complete','script':'add/update/delete group; group_members operation','source':'Features/AppGroups.svelte'},
    {'feature':'row_design_groups.create_edit_delete','status':'complete','script':'add/update/delete row_design_group; design_group_members operation','source':'Features/AppDesignGroups.svelte'},
    {'feature':'choice_design_groups.create_edit_delete','status':'complete','script':'add/update/delete choice_design_group; design_group_members operation','source':'Features/AppDesignGroups.svelte'},
    {'feature':'global_requirements.create_edit_delete','status':'complete','script':'add/update/delete global_requirement','source':'Features/AppGlobalRequirements.svelte'},
    {'feature':'sound_effects.create_edit_delete','status':'complete','script':'add/update/delete sound_effect; sound-effect import FILE','source':'Features/AppSoundEffects.svelte','note':'File import accepts the same mp3/wav/ogg/m4a/aac extensions and stores a data URL.'},
    {'feature':'categories.create_rename_delete','status':'complete','script':'add/update/delete category using type:idx identity','source':'Features/AppCategories.svelte'},

    {'feature':'rows.drag_reorder','status':'complete','script':'reorder row|backpack_row','source':'AppRowList.svelte dndzone'},
    {'feature':'features.move_up_down','status':'complete','script':'reorder point|variable|word|group|row_design_group|choice_design_group|global_requirement|sound_effect|category','source':'Features management dialogs'},
    {'feature':'choices.drag_reorder','status':'complete','script':'reorder choice --parent ROW','source':'AppObjectList.svelte dndzone'},
    {'feature':'nested.reorder','status':'complete','script':'reorder addon|score|requirement --parent ID','source':'Creator list controls'},
    {'feature':'nested.move','status':'complete','script':'move REFERENCE --parent ID --index N','source':'structural scripting equivalent'},
    {'feature':'copy_paste.deep_clone','status':'complete','script':'clone REFERENCE','source':'CreatorMain.svelte copyRow/pasteRow and store.svelte.ts pasteObject'},
    {'feature':'fragment.export_import','status':'complete','script':'export-fragment / import-fragment','source':'store.svelte.ts exportData/importData'},
    {'feature':'row_settings.sort_choices','status':'complete','script':'row-choices sort','source':'AppRowSettings.svelte sortObjects'},
    {'feature':'row_settings.copy_choices','status':'complete','script':'row-choices copy','source':'AppRowSettings.svelte copyObjects'},
    {'feature':'row_settings.copy_and_delete','status':'complete','script':'row-choices copy-and-delete','source':'AppRowSettings.svelte mergeRow'},
    {'feature':'choice_settings.copy_to_row','status':'complete','script':'clone CHOICE --parent ROW','source':'AppObjectSettings.svelte copyToAnotherRow'},

    {'feature':'rich_text.result','status':'complete','script':'set typed HTML string fields directly','source':'Creator text editor','note':'The CLI writes the same HTML payload; it does not emulate mouse/toolbar gestures.'},
    {'feature':'images.assign_data_url_or_path','status':'complete','script':'style manifest, image-field, asset tooling','source':'Creator image controls'},
    {'feature':'styling.clean_all_private','status':'complete','script':'clean-private-styling PROJECT','source':'Features/AppSymbols.svelte cleanAllStyle'},
    {'feature':'styling.design_import_export','status':'complete','script':'design import|export TARGET','source':'AppDesign.svelte, AppRowSettings.svelte, AppObjectSettings.svelte, Features/AppPrivateDesign.svelte','note':'Supports global, Row, Choice, Row Design Group, and Choice Design Group targets with Creator scope filtering.'},
    {'feature':'images.compress_convert','status':'complete','script':'compress / asset-probe','source':'release asset workflow','note':'This is more automation than the Creator provides.'},
    {'feature':'images.interactive_crop','status':'complete','script':'crop-image or crop-field with --box, or --aspect plus --position','source':'store/ImageUpload.svelte','note':'Explicit pixel boxes expose the complete crop result space; aspect mode uses the Creator 3x3 position convention and outputs WebP.'},

    {'feature':'export.separate_images_zip','status':'complete','script':'export-project PROJECT -o package.zip','source':'AppSaveLoad.svelte exportZip/imageSeparation'},
    {'feature':'export.playable_web_package','status':'complete_with_input','script':'build-viewer PROJECT --template OFFICIAL_VIEWER_ZIP -o viewer.zip','source':'AppSaveLoad.svelte exportWithViewer','note':'Requires the official viewer template ZIP so version identity is explicit.'},
    {'feature':'build.native_build_form_import_export','status':'complete','script':'build-string PROJECT export|import','source':'AppBuildForm.svelte + store.svelte.ts getSelectedObjectId/loadActivated','note':'Preserves repeat counts, random Score results, random activation results, custom words, uploaded-image payloads, Variables, and imported row-button random point results.'},
    {'feature':'build.human_summary','status':'complete','script':'build-summary PROJECT [--separate-rows]','source':'AppBuildForm.svelte getSelectedObjectName'},
    {'feature':'viewer.row_buttons','status':'complete','script':'row-button PROJECT ROW_ID; session/play row_button action','source':'viewer/AppRow.svelte buttonActivate','note':'Covers random Choice buttons, weighted random, only-unselected behavior, Variable buttons, and random Point-add buttons.'},

    {'feature':'viewer.download_rendered_image','status':'browser_only','script':'build-viewer then use the real Viewer capture/download action','source':'DlgBackpack.svelte + store.svelte.ts downloadAsImage','note':'DOM layout and computed styles are required to produce the same image.'},
    {'feature':'preview.audio_media_controls','status':'browser_only','script':'build-viewer then use the real Viewer/Creator media controls','source':'CreatorMain.svelte and Features/AppSoundEffects.svelte','note':'Playback is browser runtime behavior; authored BGM/SFX fields remain fully scriptable.'},
    {'feature':'preview.browser_rendering','status':'browser_only','script':'build-viewer then open in the real Viewer','source':'Creator live preview','note':'CSS layout, browser media playback, and DOM rendering remain browser responsibilities.'},
    {'feature':'browser.theme_and_dialog_state','status':'not_project_data','script':None,'source':'Creator UI','note':'These controls do not change the exported CYOA project.'},
]


def gui_parity_report() -> dict[str, Any]:
    counts: dict[str, int] = {}
    for item in _FEATURES:
        counts[item['status']] = counts.get(item['status'], 0) + 1
    gaps = [item for item in _FEATURES if item['status'] == 'gap']
    return {
        'format': 'iccplus-gui-parity',
        'tool_version': __version__,
        'target': {'icc_plus_version':'2.10.7','source_commit':SOURCE_COMMIT},
        'scope': 'Creator authoring outcomes and export actions',
        'source_audit': {
            'creator_components_audited': 57,
            'root': 'ICCPlus/src/lib/creator',
            'method': 'function/GUI-action inventory at the pinned commit plus store behavior checks for shared actions',
        },
        'typed_kinds': catalog_kinds(),
        'summary': {
            'features': len(_FEATURES),
            'counts': counts,
            'remaining_first_class_gaps': len(gaps),
            'complete_for_project_data': all(x['status'] != 'gap' for x in _FEATURES if x['status'] not in {'browser_only','not_project_data'}),
        },
        'features': _FEATURES,
        'gaps': gaps,
    }
