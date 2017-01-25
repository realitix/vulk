from contextlib import contextmanager

from vulk import vulkanconstant as vc
from vulk import vulkanobject as vo


class CommandBufferSynchronizedPool():
    '''This class allows to synchronize command buffers with semaphores.
    If you need a unknow quantity of command buffer to be executed with
    synchronization, this class is for you. It handles command buffer
    pooling and synchronization.

    *Exemple:*

    ```
    cbpool = CommandBufferSynchronizedChain(context)
    cbpool.begin(context, semaphore) #Must be called each frame before begining
    for action in actions:
        with cbpool.pull() as commanbuffer:
            # Register command in command buffer
    semaphore_out = cbpool.end()
    ```
    '''

    def __init__(self, context):
        '''
        *Parameters:*

        - `context`: `VulkContext`
        '''
        self.commandpool = self.init_commandpool(context)
        self.commandbuffers = []
        self.commandbuffer_id = 0
        self.semaphores = []
        self.semaphore_id = 0
        self.context = None
        self.semaphores_in = []
        self.wait_semaphores = []
        self.signal_semaphores = []

    def init_commandpool(self, context):
        '''Initialize transient command pool

        *Parameters:*

        - `context`: `VulkContext`
        '''
        flags = vc.CommandPoolCreate.TRANSIENT | vc.CommandPoolCreate.RESET_COMMAND_BUFFER # noqa
        return vo.CommandPool(
            context, context.queue_family_indices['graphic'], flags)

    def begin(self, context, semaphores=None):
        '''
        Begin pooling and synchronization of command buffers.

        *Parameters:*

        - `context`: `VulkContext`
        - `semaphores`: `list` of `Semaphore` to wait on

        **Note: `context` is borrowed until `end` is called**
        '''
        self.context = context
        self.commandbuffer_id = -1
        self.semaphore_id = -1
        self.semaphores_in.extend(semaphores if semaphores else [])

    def next_commandbuffer(self):
        '''
        Create a new command buffer if requested
        '''
        self.commandbuffer_id += 1

        try:
            cb = self.commandbuffers[self.commandbuffer_id]
        except IndexError:
            cb = self.commandpool.allocate_buffers(
                self.context, vc.CommandBufferLevel.PRIMARY, 1)[0]
            self.commandbuffers.append(cb)

        cb.reset()
        return cb

    def next_semaphore(self):
        '''
        Create a new semaphore if requested
        '''
        self.semaphore_id += 1

        try:
            semaphore = self.semaphores[self.semaphore_id]
        except IndexError:
            semaphore = vo.Semaphore(self.context)
            self.semaphores.append(semaphore)

    @contextmanager
    def pull(self):
        '''
        Pull a new command buffer.
        This function is a context manager, you should call it with
        `with` keyword to auto-submit the previous create buffer.

        *Returns:*

        `CommandBufferRegister` ready to register commands
        '''
        try:
            cb = self.next_commandbuffer()
            flags = vc.CommandBufferUsage.ONE_TIME_SUBMIT
            with cb.bind(flags) as cmd:
                yield cmd
        finally:
            self.submit()

    def submit(self):
        '''
        Submit the last command buffer
        '''
        cb_id = self.commandbuffer_id
        self.next_semaphore()
        wait_semaphores = []
        signal_semaphores = [self.semaphores[self.semaphore_id]]

        if self.semaphore_id == 0:  # First submit
            wait_semaphores.extend(self.semaphores_in)
        else:
            wait_semaphores.append(self.semaphores[self.semaphore_id - 1])

        submit = vo.SubmitInfo(
            wait_semaphores, [vc.PipelineStage.VERTEX_INPUT],
            signal_semaphores, [self.commandbuffers[cb_id]])
        vo.submit_to_graphic_queue(self.context, [submit])

    def end(self):
        '''
        Release the context.

        *Returns:*

        Out `Semaphore`: Signal semaphore of last command buffer
        '''
        del self.semaphores_in[:]
        self.context = None
        return self.semaphores[self.semaphore_id]
