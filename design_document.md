Nomenclature
============


app_spec has 'sections': opts, sources, transforms, views
each of these sections has 'elements' ('flux_element'?) which are specs, eg:

```yaml

    base_src:
      type: table_source
      source: main
      table: test_data

```

When the constructor resolves these, it creates an 'element instance'


Planned Features
================

Introduce ``Variables`` as a new 'section', these map one-to-one to widgets and can be 
referenced in the yaml spec to act as reusable value/widget pair. 
(See lumen variables)