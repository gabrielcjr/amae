from django.db import models


class Page(models.Model):
    title = models.CharField('Título', max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField('Conteúdo')
    is_published = models.BooleanField('Publicada', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Página'
        verbose_name_plural = 'Páginas'

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField('Pergunta', max_length=300)
    answer = models.TextField('Resposta')
    category = models.CharField('Categoria', max_length=100)
    order = models.PositiveIntegerField('Ordem', default=0)
    is_published = models.BooleanField('Publicada', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'order']
        verbose_name = 'Pergunta Frequente'
        verbose_name_plural = 'Perguntas Frequentes'

    def __str__(self):
        return self.question


class Testimonial(models.Model):
    author_name = models.CharField('Nome do autor', max_length=200)
    author_role = models.CharField('Função', max_length=200, blank=True)
    content = models.TextField('Depoimento')
    mission_field = models.ForeignKey(
        'missions.MissionField',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Campo missionário',
    )
    is_published = models.BooleanField('Publicado', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Testemunho'
        verbose_name_plural = 'Testemunhos'

    def __str__(self):
        return f"{self.author_name} - {self.author_role}"


class SiteImage(models.Model):
    key = models.SlugField('Identificador', unique=True, help_text='Ex: home_hero, login_side')
    description = models.CharField('Descrição', max_length=200, help_text='Onde esta imagem é usada')
    image = models.ImageField('Imagem (upload)', upload_to='site/', blank=True)
    external_url = models.URLField('URL externa', blank=True, help_text='URL de imagem externa (ex: Unsplash)')
    alt_text = models.CharField('Texto alternativo', max_length=300, blank=True)

    class Meta:
        ordering = ['key']
        verbose_name = 'Imagem do Site'
        verbose_name_plural = 'Imagens do Site'

    def __str__(self):
        return f"{self.key} - {self.description}"

    @property
    def url(self):
        if self.image:
            return self.image.url
        return self.external_url


class ContactMessage(models.Model):
    name = models.CharField('Nome', max_length=200)
    email = models.EmailField('E-mail')
    subject = models.CharField('Assunto', max_length=300)
    message = models.TextField('Mensagem')
    is_read = models.BooleanField('Lida', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mensagem de Contato'
        verbose_name_plural = 'Mensagens de Contato'

    def __str__(self):
        return f"{self.name} - {self.subject}"
