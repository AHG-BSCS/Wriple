// options.js
import { OPTIONS } from './constants.js';

// Internal storage of the current selections
let currentParams = {
  class_label: null,
  target_count: null,
  state: null,
  activity: null,
  angle: null,
  distance_t1: null,
  obstructed: null,
  obstruction: null,
  spacing: null
};

function populateSelect(selectElem, options, allowedValues = null) {
  if (!selectElem) return;
  selectElem.innerHTML = '';
  options.forEach(opt => {
    if (!allowedValues || allowedValues.includes(opt.value)) {
      const option = document.createElement('option');
      option.value = opt.value;
      option.textContent = opt.label;
      selectElem.appendChild(option);
    }
  });
}

function updateOptionsForClass(classValue, selects) {
  const { targetSelection, stateSelection, activitySelection, angleSelection, distanceSelection } = selects;
  if (classValue === '0') { // Absence
    populateSelect(targetSelection, OPTIONS.target, [OPTIONS.target[0].value]);
    populateSelect(stateSelection, OPTIONS.state, [OPTIONS.state[0].value]);
    populateSelect(activitySelection, OPTIONS.activity, [OPTIONS.activity[0].value]);
    populateSelect(angleSelection, OPTIONS.angle, [OPTIONS.angle[0].value]);
    populateSelect(distanceSelection, OPTIONS.distance, [OPTIONS.distance[0].value]);
  } else if (classValue === '1') { // Presence
    populateSelect(targetSelection, OPTIONS.target, OPTIONS.target.slice(1).map(opt => opt.value));
    populateSelect(stateSelection, OPTIONS.state, OPTIONS.state.slice(1).map(opt => opt.value));
    populateSelect(activitySelection, OPTIONS.activity, [OPTIONS.activity[1].value, OPTIONS.activity[2].value]);
    populateSelect(angleSelection, OPTIONS.angle, OPTIONS.angle.slice(1).map(opt => opt.value));
    populateSelect(distanceSelection, OPTIONS.distance, OPTIONS.distance.slice(1).map(opt => opt.value));
  }
}

function updateObstructionOptions(obstructedValue, obstructionSelection) {
  if (!obstructionSelection) return;
  if (obstructedValue === '0') { // Not obstructed
    populateSelect(obstructionSelection, OPTIONS.obstruction, [OPTIONS.obstruction[0].value]);
  } else {
    populateSelect(obstructionSelection, OPTIONS.obstruction, OPTIONS.obstruction.slice(1).map(opt => opt.value));
  }
}

function updateActivityOptions(stateValue, activitySelection) {
  if (!activitySelection) return;
  if (stateValue === '0') {
    populateSelect(activitySelection, OPTIONS.activity, [OPTIONS.activity[0].value]);
  } else if (stateValue === '1') {
    populateSelect(activitySelection, OPTIONS.activity, [OPTIONS.activity[1].value, OPTIONS.activity[2].value]);
  } else if (stateValue === '2') {
    populateSelect(activitySelection, OPTIONS.activity, OPTIONS.activity.slice(1).map(opt => opt.value));
  }
}

// Internal helper to update currentParams
function captureParams(selects) {
  currentParams = {
    class_label: selects.classSelection.value,
    target_count: selects.targetSelection.value,
    state: selects.stateSelection.value,
    activity: selects.activitySelection.value,
    angle: selects.angleSelection.value,
    distance_t1: selects.distanceSelection.value,
    obstructed: selects.obstructedSelection.value,
    obstruction: selects.obstructionSelection.value,
    spacing: selects.spacingSelection.value
  };
}

export const OptionsUI = {
  init(selects) {
    // Populate initial dropdowns
    populateSelect(selects.classSelection, OPTIONS.class);
    populateSelect(selects.targetSelection, OPTIONS.target);
    populateSelect(selects.stateSelection, OPTIONS.state);
    populateSelect(selects.activitySelection, OPTIONS.activity);
    populateSelect(selects.angleSelection, OPTIONS.angle);
    populateSelect(selects.distanceSelection, OPTIONS.distance);
    populateSelect(selects.obstructedSelection, OPTIONS.obstructed);
    populateSelect(selects.obstructionSelection, OPTIONS.obstruction);
    populateSelect(selects.spacingSelection, OPTIONS.spacing);

    // Apply initial restrictions
    updateOptionsForClass(selects.classSelection.value, selects);
    updateObstructionOptions(selects.obstructedSelection.value, selects.obstructionSelection);

    // Store initial params
    captureParams(selects);

    // Event listeners for dependent dropdowns
    selects.classSelection.addEventListener('change', e => {
      updateOptionsForClass(e.target.value, selects);
      captureParams(selects);
    });

    selects.obstructedSelection.addEventListener('change', e => {
      updateObstructionOptions(e.target.value, selects.obstructionSelection);
      captureParams(selects);
    });

    selects.stateSelection.addEventListener('change', e => {
      updateActivityOptions(e.target.value, selects.activitySelection);
      captureParams(selects);
    });

    // Change listener for *all* dropdowns to update currentParams
    [
      selects.targetSelection,
      selects.activitySelection,
      selects.angleSelection,
      selects.distanceSelection,
      selects.obstructionSelection,
      selects.spacingSelection
    ].forEach(sel => {
      if (!sel) return;
      sel.addEventListener('change', () => captureParams(selects));
    });
  },

  getSelectedParameters() {
    return { ...currentParams };
  }
};
