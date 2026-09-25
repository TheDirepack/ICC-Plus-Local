# Automatic image compression

Image compression is part of image assignment, not a separate workflow.

When `style` or `media` assigns a local file or embedded image, ICC Plus Local runs the shared optimizer automatically before the final image value is written. Bulk image assignments use the same path, so every image receives the same treatment without an extra command.

Remote image URLs stay remote. The tool does not download a URL only to recompress it.

Compression failures are reported as part of the image edit that triggered them. There is no normal post-processing pass for an LLM or user to remember.
