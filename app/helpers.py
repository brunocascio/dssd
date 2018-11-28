def parseBonitaProduct(variables, parsed = {}):
  for v in variables:
    if v['type'].lower() == 'java.lang.boolean':
      parsed[v['name']] = True if v['value'] == 'true' else False
    else:
      parsed[v['name']] = v['value']
  return parsed