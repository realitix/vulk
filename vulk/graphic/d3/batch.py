class ModelBatch():
    def begin(self, context):
        self.context = context

    def end(self):
        self.context = None

    def flush(self):
        """Flush all draws to graphic card

        Currently, flush register and submit command.

        Args:
            context (VulkContext)
        """
        # Upload mesh data
        self.mesh.upload(self.context)

        # Bind texture
        descriptorset = self.get_descriptor(self.context, self.last_texture)

        # Compute indices count
        sprites_in_batch = self.idx / 4  # 4 idx per vertex
        indices_count = int(sprites_in_batch) * 6

        # Register commands
        with self.cbpool.pull() as cmd:
            width = self.context.width
            height = self.context.height
            cmd.begin_renderpass(
                self.renderpass,
                self.framebuffer,
                vo.Rect2D(vo.Offset2D(0, 0),
                          vo.Extent2D(width, height)),
                []
            )
            cmd.bind_pipeline(self.pipeline)
            self.mesh.bind(cmd)
            cmd.bind_descriptor_sets(self.pipelinelayout, 0,
                                     [descriptorset], [])
            self.mesh.draw(cmd, 0, indices_count)
            cmd.end_renderpass()

        self.idx = 0
