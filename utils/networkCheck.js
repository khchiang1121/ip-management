function check(
    networks,
    sources,
    type = ['ip', 'cidr', 'hostsubnet'],
    allowMissingFields = {},
    fieldsToCheck = {},
    allowNullFields = {}
) {
    // Helper function to check if two values are the same
    function areValuesSame(a, b) {
        // Check if both are strings
        if (typeof a === 'string' && typeof b === 'string') {
            return a === b;
        }

        // Check if both are arrays
        if (Array.isArray(a) && Array.isArray(b)) {
            // Quick length check
            if (a.length !== b.length) return false;

            // Count frequencies of elements in both arrays using plain object
            const countMap = {};

            for (const item of a) {
                countMap[item] = (countMap[item] || 0) + 1;
            }

            for (const item of b) {
                if (!countMap[item] || countMap[item] === 0) {
                    return false;
                }
                countMap[item] -= 1;
            }

            return true;
        }

        // If not string or array, return false
        return false;
    }

    //check if type is valid
    if (!type) {
        throw new Error("Type is required.");
    }

    // check if type is an array and all elements are valid
    if (Array.isArray(type)) {
        if (!type.every(t => ['cidr', 'ip', 'hostsubnet'].includes(t))) {
            throw new Error("Invalid type.");
        }
    } else {
        // type cannot be a string
        throw new Error("Invalid type, must be an array.");
    }

    if (sources.Truth) {
        throw new Error("Cannot use Truth as a source name.");
    }

    const defaultAllowMissingFields = {
        ip: ['subnet_mask', 'mac'],
        cidr: ['cidrs'],
        hostsubnet: ['egress_ips', 'mac']
    };
    // merge default allow missing fields with user provided allow missing fields
    allowMissingFields = { ...defaultAllowMissingFields, ...allowMissingFields };

    const defaultFieldsToCheck = {
        ip: ['ip', 'subnet_mask', 'mac'],
        cidr: ['cidrs'],
        hostsubnet: ['hostname', 'egress_cidrs']
    };
    // merge default fields to check with user provided fields to check
    fieldsToCheck = { ...defaultFieldsToCheck, ...fieldsToCheck };

    const defaultAllowNullFields = {
        ip: ['subnet_mask', 'mac'],
        cidr: ['cidrs'],
        hostsubnet: ['egress_ips']
    };
    // merge default allow null fields with user provided allow null fields
    allowNullFields = { ...defaultAllowNullFields, ...allowNullFields };

    const allSources = { ...sources, Truth: { networks: networks || [] } };
    const inconsistencies = [];

    // Collect all networks by `name-type` into a unified map
    const unifiedMap = {};
    for (const sourceName in allSources) {
        const source = allSources[sourceName];
        (source.networks || []).forEach(net => {
            if (type.includes(net.type)) {
                const key = `${net.name}-${net.type}`;
                if (!unifiedMap[key]) {
                    unifiedMap[key] = [];
                }
                unifiedMap[key].push({ source: sourceName, record: net });
            }
        });
    }
    // Given all sources, collect all networks by `name-type` into a unified map
    // the key is `name-type` and the value is an array of objects with source and record
    // name and type are required, other fields are optional
    // examples: 
    // unifiedMap = {
    //   'test-cidr': [
    //     { source: 'Truth', record: { name: 'test', type: 'cidr', cidrs: ['1.1.1.1/32'] } },
    //     { source: 'source1', record: { name: 'test', type: 'cidr', cidrs: ['1.1.1.1/32'] } }
    //   ]
    // }
    //

    // Check inconsistencies for each key in the unified map
    for (const [key, entries] of Object.entries(unifiedMap)) {
        const record_name = entries[0].record.name;
        const record_type = entries[0].record.type;
        // example of  [key, entries]
        // key: 'test-cidr'
        // entries:
        // [
        //   { source: 'Truth', record: { name: 'test', type: 'cidr', cidrs: ['1.1.1.1/32'] } },
        //   { source: 'source1', record: { name: 'test', type: 'cidr', cidrs: ['1.1.1.1/32'] } }
        // ]
        const details = [];

        for (const field of fieldsToCheck[record_type]) {
            // examples
            // const fieldValuesList = [
            //     { value: "192.168.1.1", sources: ["server1", "server2"] },
            //     { value: "192.168.1.2", sources: ["server3"] },
            // ];
            const fieldValuesList = [];
            let missingCount = 0;

            entries.forEach(({ source, record }) => {
                const value = record[field];

                if (value !== undefined) {
                    // Check null values only for fields not in allowNullFields
                    if (value !== null || allowNullFields[record_type].includes(field)) {
                        if (value !== null) {

                            // Find the object with the matching IP address (value)
                            const target = fieldValuesList.find(item => areValuesSame(item.value, value));
                            
                            // If the object is found, insert the source
                            if (target) {
                                // Check if the source is already in the sources array to avoid duplicates
                                if (!target.sources.includes(source)) {
                                    target.sources.push(source);
                                }
                            } else {
                                fieldValuesList.push( ({value: value, sources: [source]}) )
                            }

                        }
                    } else {
                        missingCount++;
                    }
                } else {
                    // Allow missing fields if specified
                    if (!allowMissingFields[record_type].includes(field)) {
                        missingCount++;
                    }
                }
            });

            const uniqueValuesCount = fieldValuesList.length;
            const totalSources = entries.length;

            // Determine if it's a mismatch, missing, or both
            // if (uniqueValues.length > 1) {
            if (uniqueValuesCount > 1) {
                // Mismatch detected
                details.push({
                    field,
                    type: "mismatch",
                    values: fieldValuesList,
                    // values: Object.entries(fieldValues).map(([value, sources]) => ({ value, sources })),
                    message: `${field.toUpperCase()} mismatch across sources`
                });
            }

            if (missingCount > 0 && !allowMissingFields[record_type].includes(field) && missingCount < totalSources) {
                // Missing values detected
                details.push({
                    field,
                    type: "missing",
                    missingSources: entries.filter(e => !e.record[field]).map(e => e.source),
                    message: `${field.toUpperCase()} missing in some sources`
                });
            }

            // if (uniqueValuesCount > 1 && missingCount > 0) {
            // // if (uniqueValues.length > 1 && missingCount > 0) {
            //     // Both mismatch and missing detected
            //     details.push({
            //         field,
            //         values: fieldValuesList,
            //         // values: Object.entries(fieldValues).map(([value, sources]) => ({ value, sources })),
            //         missingSources: entries.filter(e => !e.record[field]).map(e => e.source),
            //         message: `${field.toUpperCase()} mismatch and missing in some sources`
            //     });
            // }
        }

        if (details.length > 0) {
            inconsistencies.push({
                name: record_name,
                type: record_type,
                key,
                sources: entries.map(e => e.source),
                details
            });
        }
    }

    return inconsistencies;
}